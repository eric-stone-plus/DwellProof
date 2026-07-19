mod reasonix;

use reasonix::acp::{message_chunk_text, AcpClient};
use reasonix::audit::AuditLog;
use reasonix::credentials::{resolve_api_key, CredentialBridge};
use reasonix::home::{prepare, ReasonixHome};
use reasonix::manifest::{platform_key, resolve_binary_path, PINNED_VERSION};
use reasonix::policy::{has_citation, MAX_QUESTION_CHARS, MAX_SNAPSHOT_CHARS};
use reasonix::ReasonixError;
use serde::Serialize;
use serde_json::{json, Value};
use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use tauri::ipc::Channel;
use tauri::{AppHandle, Manager, State};

type Shared<T> = Arc<Mutex<T>>;

struct ReasonixState {
    home: Option<ReasonixHome>,
    audit: Option<AuditLog>,
    client: Option<AcpClient>,
}

impl ReasonixState {
    fn new() -> Self {
        Self {
            home: None,
            audit: None,
            client: None,
        }
    }
}

const CASE_ID: &str = "GZ-DEMO-001";

fn disabled() -> bool {
    std::env::var("DWELLPROOF_REASONIX_ENABLED")
        .map(|value| value == "0")
        .unwrap_or(false)
}

#[derive(Serialize)]
struct ReasonixStatus {
    status: &'static str,
    reason: Option<String>,
    version: &'static str,
    model: &'static str,
    platform: &'static str,
}

fn compute_status() -> ReasonixStatus {
    let base = |status: &'static str, reason: Option<String>| ReasonixStatus {
        status,
        reason,
        version: PINNED_VERSION,
        model: "deepseek-v4-pro",
        platform: platform_key(),
    };
    if disabled() {
        return base("disabled", None);
    }
    if let Err(error) = resolve_binary_path() {
        return base("unavailable", Some(error.message));
    }
    if let Err(error) = resolve_api_key() {
        return base("setup_required", Some(error.message));
    }
    base("available", None)
}

#[tauri::command]
fn reasonix_status() -> ReasonixStatus {
    compute_status()
}

#[derive(Serialize)]
struct ExplainResult {
    text: String,
    citations_ok: bool,
    usage_unavailable: bool,
    session_id: String,
}

fn ensure_home_and_audit(
    app: &AppHandle,
    state: &mut ReasonixState,
) -> reasonix::Result<()> {
    if state.home.is_none() {
        let config_dir = app
            .path()
            .app_config_dir()
            .map_err(|error| ReasonixError::new("HOME_PREP_FAILED", error.to_string()))?;
        state.home = Some(prepare(&config_dir.join("reasonix"))?);
    }
    if state.audit.is_none() {
        let data_dir = app
            .path()
            .app_data_dir()
            .map_err(|error| ReasonixError::new("AUDIT_FAILED", error.to_string()))?;
        state.audit = Some(AuditLog::new(&data_dir)?);
    }
    Ok(())
}

/// One full explain turn: (re)start the runtime, open a session, stream the
/// prompt. `restart` forces a fresh process and is used once for recovery.
fn run_explain_turn(
    app: &AppHandle,
    state: &mut ReasonixState,
    binary: &PathBuf,
    api_key: &str,
    prompt_text: &str,
    on_event: &Channel<Value>,
    restart: bool,
) -> reasonix::Result<ExplainResult> {
    ensure_home_and_audit(app, state)?;
    let home = state.home.clone().expect("home prepared above");

    if restart {
        state.client = None;
    }
    if state.client.is_none() {
        reasonix::home::reset_workspace(&home)?;
        state.client = Some(AcpClient::start(binary, &home)?);
    }
    let client = state.client.as_mut().expect("client started above");

    let session_id = match client.session_id() {
        Some(existing) if !restart => existing.to_string(),
        _ => {
            let bridge = CredentialBridge::create(&home, api_key)?;
            let result = client.new_session();
            drop(bridge);
            result?
        }
    };

    let mut text = String::new();
    let prompt_result = client.prompt(prompt_text, |update| {
        if let Some(chunk) = message_chunk_text(update) {
            text.push_str(chunk);
            let _ = on_event.send(json!({ "type": "chunk", "text": chunk }));
        }
    });

    match prompt_result {
        Ok(_) => {
            let citations_ok = has_citation(&text);
            if let Some(audit) = &state.audit {
                let _ = audit.record_event(
                    "explain",
                    CASE_ID,
                    Some(&session_id),
                    Some(prompt_text),
                    Some(&text),
                    if citations_ok { "ok" } else { "citation_rejected" },
                );
            }
            Ok(ExplainResult {
                text,
                citations_ok,
                usage_unavailable: true,
                session_id,
            })
        }
        Err(error) => {
            if let Some(audit) = &state.audit {
                let _ = audit.record_event(
                    "explain",
                    CASE_ID,
                    Some(&session_id),
                    Some(prompt_text),
                    None,
                    &error.code,
                );
            }
            Err(error)
        }
    }
}

fn explain_blocking(
    app: AppHandle,
    state: Shared<ReasonixState>,
    question: String,
    snapshot: String,
    on_event: Channel<Value>,
) -> Result<ExplainResult, ReasonixError> {
    if disabled() {
        return Err(ReasonixError::new(
            "DISABLED",
            "Reasonix integration is disabled (DWELLPROOF_REASONIX_ENABLED=0)",
        ));
    }
    if question.chars().count() > MAX_QUESTION_CHARS {
        return Err(ReasonixError::new(
            "INVALID_PROMPT",
            format!("question exceeds {MAX_QUESTION_CHARS} characters"),
        ));
    }
    if snapshot.chars().count() > MAX_SNAPSHOT_CHARS {
        return Err(ReasonixError::new(
            "INVALID_PROMPT",
            format!("case snapshot exceeds {MAX_SNAPSHOT_CHARS} characters"),
        ));
    }
    let binary = resolve_binary_path()?;
    let api_key = resolve_api_key()?;

    let prompt_text = format!(
        "以下是案例 GZ-DEMO-001 的只读证据快照。只能基于它回答，不得补充快照外的事实。\n\n\
         <case-snapshot>\n{snapshot}\n</case-snapshot>\n\n\
         用户问题：{question}\n\n\
         回答要求：中文、简明；每个涉及案例事实的论断都引用 G01-G07 或 deed-tax、nbs-index、lpr；\
         不给买入/卖出建议；快照无法支撑时直接说明缺哪一项检查。"
    );

    let mut guard = state
        .lock()
        .map_err(|_| ReasonixError::new("PROCESS_EXITED", "Reasonix state lock poisoned"))?;
    match run_explain_turn(&app, &mut guard, &binary, &api_key, &prompt_text, &on_event, false) {
        Ok(result) => Ok(result),
        Err(error) if error.code == "PROCESS_EXITED" || error.code == "RPC_ERROR" => {
            // One recovery attempt with a fresh process and session.
            let _ = on_event.send(json!({ "type": "status", "state": "restarting" }));
            run_explain_turn(&app, &mut guard, &binary, &api_key, &prompt_text, &on_event, true)
        }
        Err(error) => Err(error),
    }
}

#[tauri::command]
async fn reasonix_explain(
    app: AppHandle,
    state: State<'_, Shared<ReasonixState>>,
    question: String,
    snapshot: String,
    on_event: Channel<Value>,
) -> Result<ExplainResult, ReasonixError> {
    let shared = state.inner().clone();
    tauri::async_runtime::spawn_blocking(move || {
        explain_blocking(app, shared, question, snapshot, on_event)
    })
    .await
    .map_err(|error| ReasonixError::new("PROCESS_EXITED", error.to_string()))?
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(Arc::new(Mutex::new(ReasonixState::new())) as Shared<ReasonixState>)
        .invoke_handler(tauri::generate_handler![reasonix_status, reasonix_explain])
        .run(tauri::generate_context!())
        .expect("failed to run DwellProof desktop application");
}

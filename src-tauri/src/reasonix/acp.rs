//! Minimal ACP v1 (NDJSON over stdio) client for the pinned Reasonix binary.
//!
//! The protocol mirrors COFORGE's `acp-client.ts`, re-implemented in Rust:
//! `initialize`, `session/new`, `session/prompt`, `session/cancel`, streamed
//! `session/update` notifications, and inbound `session/request_permission`
//! (always cancelled — DwellProof grants no tool permissions). Any tool call
//! from the runtime is a policy violation that cancels the turn.

use super::home::ReasonixHome;
use super::manifest::PROTOCOL_VERSION;
use super::policy::MAX_FRAME_BYTES;
use super::{ReasonixError, Result};
use serde_json::{json, Value};
use std::collections::HashMap;
use std::io::{BufRead, BufReader, Read, Write};
use std::process::{Child, ChildStdin, Command, Stdio};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{mpsc, Arc, Mutex};
use std::time::{Duration, Instant};

const HANDSHAKE_TIMEOUT: Duration = Duration::from_secs(30);
pub const PROMPT_TIMEOUT: Duration = Duration::from_secs(240);

type PendingMap = Arc<Mutex<HashMap<u64, mpsc::Sender<Result<Value>>>>>;

pub struct AcpClient {
    child: Child,
    stdin: Arc<Mutex<ChildStdin>>,
    pending: PendingMap,
    updates_rx: mpsc::Receiver<Value>,
    violation: Arc<Mutex<Option<ReasonixError>>>,
    alive: Arc<AtomicBool>,
    next_id: u64,
    session_id: Option<String>,
    workspace: std::path::PathBuf,
}

fn invalid(message: impl Into<String>) -> ReasonixError {
    ReasonixError::new("PROTOCOL_ERROR", message)
}

fn write_frame(stdin: &Arc<Mutex<ChildStdin>>, frame: &Value) -> Result<()> {
    let mut line = serde_json::to_string(frame)
        .map_err(|error| invalid(format!("cannot encode ACP frame: {error}")))?;
    line.push('\n');
    let mut guard = stdin
        .lock()
        .map_err(|_| ReasonixError::new("PROCESS_EXITED", "ACP stdin lock poisoned"))?;
    guard
        .write_all(line.as_bytes())
        .and_then(|()| guard.flush())
        .map_err(|error| {
            ReasonixError::new("PROCESS_EXITED", format!("cannot write to Reasonix: {error}"))
        })
}

impl AcpClient {
    /// Spawn the verified binary inside the isolated home and complete the
    /// `initialize` handshake, including the protocol version check.
    pub fn start(binary: &std::path::Path, home: &ReasonixHome) -> Result<Self> {
        let mut command = Command::new(binary);
        command
            .args(["acp", "--model", "deepseek-pro", "--profile", "balanced"])
            .current_dir(&home.workspace)
            .env_clear()
            .envs(super::home::process_env(home))
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());
        let mut child = command.spawn().map_err(|error| {
            ReasonixError::new("SPAWN_FAILED", format!("cannot start Reasonix: {error}"))
        })?;

        let stdin = child
            .stdin
            .take()
            .ok_or_else(|| ReasonixError::new("SPAWN_FAILED", "Reasonix stdin unavailable"))?;
        let stdout = child
            .stdout
            .take()
            .ok_or_else(|| ReasonixError::new("SPAWN_FAILED", "Reasonix stdout unavailable"))?;
        let stderr = child
            .stderr
            .take()
            .ok_or_else(|| ReasonixError::new("SPAWN_FAILED", "Reasonix stderr unavailable"))?;

        let stdin = Arc::new(Mutex::new(stdin));
        let pending: PendingMap = Arc::new(Mutex::new(HashMap::new()));
        let violation: Arc<Mutex<Option<ReasonixError>>> = Arc::new(Mutex::new(None));
        let alive = Arc::new(AtomicBool::new(true));
        let (updates_tx, updates_rx) = mpsc::channel::<Value>();

        // Stdout reader: NDJSON framing, response routing, update forwarding,
        // inbound permission/policy handling.
        {
            let pending = Arc::clone(&pending);
            let violation = Arc::clone(&violation);
            let alive = Arc::clone(&alive);
            let stdin = Arc::clone(&stdin);
            std::thread::spawn(move || {
                let mut reader = BufReader::new(stdout);
                loop {
                    let mut buffer: Vec<u8> = Vec::new();
                    match reader.read_until(b'\n', &mut buffer) {
                        Ok(0) => break,
                        Ok(_) => {
                            if buffer.len() > MAX_FRAME_BYTES {
                                set_violation(
                                    &violation,
                                    ReasonixError::new(
                                        "PROTOCOL_ERROR",
                                        "Reasonix frame exceeded the size cap",
                                    ),
                                );
                                continue;
                            }
                            let frame: Value = match serde_json::from_slice(&buffer) {
                                Ok(frame) => frame,
                                Err(_) => continue,
                            };
                            handle_frame(&frame, &pending, &violation, &stdin, &updates_tx);
                        }
                        Err(_) => break,
                    }
                }
                alive.store(false, Ordering::SeqCst);
                if let Ok(mut pending) = pending.lock() {
                    for (_, sender) in pending.drain() {
                        let _ = sender.send(Err(ReasonixError::new(
                            "PROCESS_EXITED",
                            "Reasonix ACP process exited",
                        )));
                    }
                }
            });
        }

        // Stderr reader: keep the tail for diagnostics.
        {
            std::thread::spawn(move || {
                let mut buffer = [0u8; 4096];
                let mut reader = BufReader::new(stderr);
                loop {
                    match reader.read(&mut buffer) {
                        Ok(0) | Err(_) => break,
                        Ok(_) => {}
                    }
                }
            });
        }

        let mut client = Self {
            child,
            stdin,
            pending,
            updates_rx,
            violation,
            alive,
            next_id: 0,
            session_id: None,
            workspace: home.workspace.clone(),
        };

        let result = client.request(
            "initialize",
            json!({
                "protocolVersion": PROTOCOL_VERSION,
                "clientInfo": { "name": "dwellproof", "title": "DwellProof", "version": "0.1.0" },
                "clientCapabilities": {},
            }),
            HANDSHAKE_TIMEOUT,
        )?;
        let version = result
            .get("protocolVersion")
            .and_then(Value::as_u64)
            .ok_or_else(|| invalid("initialize result is missing protocolVersion"))?;
        if version != PROTOCOL_VERSION {
            let _ = client.stop();
            return Err(ReasonixError::new(
                "PROTOCOL_MISMATCH",
                format!(
                    "Reasonix protocol {version} does not match pinned {PROTOCOL_VERSION}"
                ),
            ));
        }
        Ok(client)
    }

    pub fn session_id(&self) -> Option<&str> {
        self.session_id.as_deref()
    }

    pub fn is_alive(&self) -> bool {
        self.alive.load(Ordering::SeqCst)
    }

    fn send_request(
        &mut self,
        method: &str,
        params: Value,
    ) -> Result<mpsc::Receiver<Result<Value>>> {
        if !self.is_alive() {
            return Err(ReasonixError::new(
                "PROCESS_EXITED",
                "Reasonix ACP process is not running",
            ));
        }
        self.next_id += 1;
        let id = self.next_id;
        let (sender, receiver) = mpsc::channel();
        self.pending
            .lock()
            .map_err(|_| ReasonixError::new("PROCESS_EXITED", "ACP state lock poisoned"))?
            .insert(id, sender);
        let frame = json!({ "jsonrpc": "2.0", "id": id, "method": method, "params": params });
        if let Err(error) = write_frame(&self.stdin, &frame) {
            if let Ok(mut pending) = self.pending.lock() {
                pending.remove(&id);
            }
            return Err(error);
        }
        Ok(receiver)
    }

    fn request(&mut self, method: &str, params: Value, timeout: Duration) -> Result<Value> {
        let receiver = self.send_request(method, params)?;
        match receiver.recv_timeout(timeout) {
            Ok(result) => result,
            Err(mpsc::RecvTimeoutError::Timeout) => Err(ReasonixError::new(
                "REQUEST_TIMEOUT",
                format!("ACP request {method} timed out"),
            )),
            Err(mpsc::RecvTimeoutError::Disconnected) => Err(ReasonixError::new(
                "PROCESS_EXITED",
                "Reasonix ACP response channel closed",
            )),
        }
    }

    pub fn new_session(&mut self) -> Result<String> {
        let result = self.request(
            "session/new",
            json!({ "cwd": self.workspace.display().to_string(), "mcpServers": [] }),
            HANDSHAKE_TIMEOUT,
        )?;
        let session_id = result
            .get("sessionId")
            .and_then(Value::as_str)
            .ok_or_else(|| invalid("session/new result is missing sessionId"))?
            .to_string();
        self.session_id = Some(session_id.clone());
        Ok(session_id)
    }

    /// Send a prompt and stream `session/update` notifications to `on_update`
    /// until the turn resolves. Tool activity is a policy violation.
    pub fn prompt<F>(&mut self, text: &str, mut on_update: F) -> Result<Value>
    where
        F: FnMut(&Value),
    {
        let session_id = self.session_id.clone().ok_or_else(|| {
            ReasonixError::new("NO_SESSION", "no active Reasonix session")
        })?;
        if text.trim().is_empty() {
            return Err(ReasonixError::new("INVALID_PROMPT", "prompt cannot be empty"));
        }
        if text.trim_start().starts_with('/') {
            return Err(ReasonixError::new(
                "INVALID_PROMPT",
                "slash commands are disabled",
            ));
        }
        if let Ok(mut violation) = self.violation.lock() {
            *violation = None;
        }
        let response_rx = self.send_request(
            "session/prompt",
            json!({
                "sessionId": session_id,
                "prompt": [{ "type": "text", "text": text }],
            }),
        )?;
        let deadline = Instant::now() + PROMPT_TIMEOUT;
        loop {
            if let Ok(result) = response_rx.try_recv() {
                // The reader thread forwards updates before routing the turn
                // result; drain anything still queued so no trailing chunk of
                // this turn is lost.
                while let Ok(update) = self.updates_rx.try_recv() {
                    on_update(&update);
                }
                if let Some(violation) = take_violation(&self.violation) {
                    return Err(violation);
                }
                return result;
            }
            match self.updates_rx.recv_timeout(Duration::from_millis(50)) {
                Ok(update) => on_update(&update),
                Err(mpsc::RecvTimeoutError::Timeout) => {}
                Err(mpsc::RecvTimeoutError::Disconnected) => {
                    return Err(ReasonixError::new(
                        "PROCESS_EXITED",
                        "Reasonix ACP update channel closed",
                    ))
                }
            }
            if let Some(violation) = take_violation(&self.violation) {
                let _ = self.cancel();
                return Err(violation);
            }
            if Instant::now() >= deadline {
                let _ = self.cancel();
                return Err(ReasonixError::new(
                    "REQUEST_TIMEOUT",
                    "Reasonix prompt timed out",
                ));
            }
        }
    }

    pub fn cancel(&mut self) -> Result<()> {
        let session_id = match &self.session_id {
            Some(session_id) => session_id.clone(),
            None => return Ok(()),
        };
        write_frame(
            &self.stdin,
            &json!({
                "jsonrpc": "2.0",
                "method": "session/cancel",
                "params": { "sessionId": session_id },
            }),
        )
    }

    pub fn stop(&mut self) -> Result<()> {
        self.alive.store(false, Ordering::SeqCst);
        let _ = self.child.kill();
        let _ = self.child.wait();
        Ok(())
    }
}

impl Drop for AcpClient {
    fn drop(&mut self) {
        let _ = self.stop();
    }
}

fn set_violation(slot: &Arc<Mutex<Option<ReasonixError>>>, error: ReasonixError) {
    if let Ok(mut guard) = slot.lock() {
        if guard.is_none() {
            *guard = Some(error);
        }
    }
}

fn take_violation(slot: &Arc<Mutex<Option<ReasonixError>>>) -> Option<ReasonixError> {
    slot.lock().ok()?.take()
}

fn handle_frame(
    frame: &Value,
    pending: &PendingMap,
    violation: &Arc<Mutex<Option<ReasonixError>>>,
    stdin: &Arc<Mutex<ChildStdin>>,
    updates_tx: &mpsc::Sender<Value>,
) {
    let id = frame.get("id").and_then(Value::as_u64);
    let method = frame.get("method").and_then(Value::as_str);

    // Response to a host request.
    if method.is_none() {
        if let Some(id) = id {
            if let Some(sender) = pending.lock().ok().and_then(|mut map| map.remove(&id)) {
                if let Some(error) = frame.get("error") {
                    let message = error
                        .get("message")
                        .and_then(Value::as_str)
                        .unwrap_or("unknown ACP error");
                    let _ = sender.send(Err(ReasonixError::new("RPC_ERROR", message)));
                } else {
                    let _ = sender.send(Ok(frame.get("result").cloned().unwrap_or(Value::Null)));
                }
            }
        }
        return;
    }

    let method = method.unwrap_or_default();
    match method {
        "session/update" => {
            // v1 registers no tools: any tool activity is a policy violation.
            let update_kind = frame
                .pointer("/params/update/sessionUpdate")
                .and_then(Value::as_str)
                .unwrap_or_default();
            if matches!(update_kind, "tool_call" | "tool_call_update") {
                set_violation(
                    violation,
                    ReasonixError::new(
                        "TOOL_POLICY_VIOLATION",
                        format!("Reasonix attempted disallowed tool activity ({update_kind})"),
                    ),
                );
            }
            if let Some(params) = frame.get("params") {
                let _ = updates_tx.send(params.clone());
            }
        }
        "session/request_permission" => {
            // DwellProof never grants permissions in shadow mode.
            if let Some(id) = id {
                let _ = write_frame(
                    stdin,
                    &json!({
                        "jsonrpc": "2.0",
                        "id": id,
                        "result": { "outcome": { "outcome": "cancelled" } },
                    }),
                );
            }
        }
        _ => {
            if let Some(id) = id {
                let _ = write_frame(
                    stdin,
                    &json!({
                        "jsonrpc": "2.0",
                        "id": id,
                        "error": { "code": -32601, "message": format!("unsupported host method: {method}") },
                    }),
                );
            }
        }
    }
}

/// Extract the text of an `agent_message_chunk` update, if this is one.
pub fn message_chunk_text(update: &Value) -> Option<&str> {
    let update = update.get("update")?;
    if update.get("sessionUpdate")?.as_str()? != "agent_message_chunk" {
        return None;
    }
    update.pointer("/content/text")?.as_str()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::reasonix::home;
    use std::fs;
    use std::os::unix::fs::PermissionsExt;

    /// A fixture "binary": a shell script replaying a canned ACP conversation.
    fn write_fixture(name: &str, body: &str) -> std::path::PathBuf {
        let path = std::env::temp_dir().join(format!("dwellproof-acp-{name}-{}", std::process::id()));
        fs::write(&path, body).expect("write fixture");
        fs::set_permissions(&path, fs::Permissions::from_mode(0o755)).expect("chmod fixture");
        path
    }

    const FIXTURE_OK: &str = r#"#!/bin/bash
while IFS= read -r line; do
  case "$line" in
    *'"initialize"'*)
      printf '%s\n' '{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":1,"agentInfo":{"name":"fixture"}}}'
      ;;
    *'"session/new"'*)
      printf '%s\n' '{"jsonrpc":"2.0","id":2,"result":{"sessionId":"fixture-session"}}'
      ;;
    *'"session/prompt"'*)
      printf '%s\n' '{"jsonrpc":"2.0","method":"session/update","params":{"sessionId":"fixture-session","update":{"sessionUpdate":"agent_message_chunk","content":{"type":"text","text":"G01 缺口："}}}}'
      printf '%s\n' '{"jsonrpc":"2.0","method":"session/update","params":{"sessionId":"fixture-session","update":{"sessionUpdate":"agent_message_chunk","content":{"type":"text","text":"缺登记证明。"}}}}'
      printf '%s\n' '{"jsonrpc":"2.0","id":3,"result":{"stopReason":"end_turn"}}'
      ;;
  esac
done
"#;

    const FIXTURE_TOOL_CALL: &str = r#"#!/bin/bash
while IFS= read -r line; do
  case "$line" in
    *'"initialize"'*)
      printf '%s\n' '{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":1}}'
      ;;
    *'"session/new"'*)
      printf '%s\n' '{"jsonrpc":"2.0","id":2,"result":{"sessionId":"fixture-session"}}'
      ;;
    *'"session/prompt"'*)
      printf '%s\n' '{"jsonrpc":"2.0","method":"session/update","params":{"sessionId":"fixture-session","update":{"sessionUpdate":"tool_call","toolCallId":"x","title":"bash"}}}'
      printf '%s\n' '{"jsonrpc":"2.0","id":3,"result":{"stopReason":"end_turn"}}'
      ;;
  esac
done
"#;

    fn test_home(tag: &str) -> (std::path::PathBuf, ReasonixHome) {
        let root = std::env::temp_dir().join(format!(
            "dwellproof-acp-home-{tag}-{}",
            std::process::id()
        ));
        let layout = home::prepare(&root).expect("prepare home");
        (root, layout)
    }

    #[test]
    fn full_turn_streams_chunks_and_completes() {
        let fixture = write_fixture("ok", FIXTURE_OK);
        let (root, layout) = test_home("full");
        let mut client = AcpClient::start(&fixture, &layout).expect("start client");
        let session = client.new_session().expect("new session");
        assert_eq!(session, "fixture-session");
        let mut chunks = Vec::new();
        let result = client
            .prompt("解释 G01 缺口", |update| {
                if let Some(text) = message_chunk_text(update) {
                    chunks.push(text.to_string());
                }
            })
            .expect("prompt");
        assert_eq!(
            result.get("stopReason").and_then(Value::as_str),
            Some("end_turn")
        );
        assert_eq!(chunks.join(""), "G01 缺口：缺登记证明。");
        client.stop().expect("stop");
        let _ = fs::remove_file(&fixture);
        let _ = fs::remove_dir_all(&root);
    }

    #[test]
    fn tool_activity_is_a_policy_violation() {
        let fixture = write_fixture("tool", FIXTURE_TOOL_CALL);
        let (root, layout) = test_home("tool");
        let mut client = AcpClient::start(&fixture, &layout).expect("start client");
        client.new_session().expect("new session");
        let error = client.prompt("hack", |_| {}).unwrap_err();
        assert_eq!(error.code, "TOOL_POLICY_VIOLATION");
        client.stop().expect("stop");
        let _ = fs::remove_file(&fixture);
        let _ = fs::remove_dir_all(&root);
    }

    #[test]
    fn prompt_rejects_empty_and_slash() {
        let fixture = write_fixture("ok2", FIXTURE_OK);
        let (root, layout) = test_home("slash");
        let mut client = AcpClient::start(&fixture, &layout).expect("start client");
        client.new_session().expect("new session");
        assert_eq!(
            client.prompt("   ", |_| {}).unwrap_err().code,
            "INVALID_PROMPT"
        );
        assert_eq!(
            client.prompt("/model x", |_| {}).unwrap_err().code,
            "INVALID_PROMPT"
        );
        client.stop().expect("stop");
        let _ = fs::remove_file(&fixture);
        let _ = fs::remove_dir_all(&root);
    }

    /// Smoke test against the real pinned binary: handshake, session creation
    /// with a fixture (never-used) credential, and bridge removal. No model
    /// call is made, so no network or valid key is required. Run with
    /// `cargo test -- --ignored` after scripts/fetch_reasonix_runtime.py.
    #[test]
    #[ignore = "requires the pinned real Reasonix binary"]
    fn real_binary_handshake() {
        let binary = crate::reasonix::manifest::resolve_binary_path()
            .expect("pinned binary must resolve");
        let (root, layout) = test_home("real");
        let mut client = AcpClient::start(&binary, &layout).expect("initialize");
        let session = {
            let bridge = crate::reasonix::credentials::CredentialBridge::create(
                &layout,
                "sk-fixture-not-a-real-key",
            )
            .expect("create bridge");
            let session = client.new_session().expect("session/new");
            drop(bridge);
            session
        };
        assert!(!session.is_empty());
        assert!(!layout.credential_bridge.exists());
        client.stop().expect("stop");
        let _ = fs::remove_dir_all(&root);
    }
}

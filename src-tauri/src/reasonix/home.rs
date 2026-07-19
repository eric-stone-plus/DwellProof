//! Isolated Reasonix home: private directories, pinned deny-all config, and a
//! filtered process environment. Mirrors the isolation semantics of COFORGE's
//! `home.ts` (Apache-2.0/MIT, see THIRD_PARTY_NOTICES.md), re-implemented in
//! Rust with DwellProof's own prompt and tool policy.

use super::{ReasonixError, Result};
use std::fs;
use std::path::{Path, PathBuf};

const SYSTEM_PROMPT: &str = "You are the read-only explanation layer embedded in DwellProof, \
an evidence workbench for a specific second-hand home transaction in China.\n\
You only explain. You never mark evidence as verified, never change readiness, gate, or risk \
state, and never calculate taxes, loans, cash flow, NPV, or IRR.\n\
You never invent rates, taxes, title facts, comparable transactions, or evidence. If the case \
snapshot cannot support an answer, say so and name the missing check.\n\
Every claim about the case must cite a stable identifier: gate codes G01-G07 or source ids \
deed-tax, nbs-index, lpr.\n\
Never request shell, filesystem, web, memory, skill, plugin, session-history, or configuration \
tools.\n\
Answer in Chinese, concisely.";

fn runtime_config() -> String {
    format!(
        r#"config_version = 4
default_model = "deepseek-pro"
credentials_store = "file"

[desktop]
check_updates = false
telemetry = false
metrics = false

[agent]
system_prompt = {system_prompt}
max_steps = 32
planner_max_steps = 0
auto_plan = "off"
memory_compiler = {{ enabled = false }}

[[providers]]
name = "deepseek-pro"
kind = "openai"
base_url = "https://api.deepseek.com"
model = "deepseek-v4-pro"
api_key_env = "DEEPSEEK_API_KEY"
context_window = 1000000
effort = "max"
supported_efforts = ["disabled", "high", "max"]
default_effort = "max"
no_proxy = true

[tools]
# Empty means every built-in upstream; this unknown sentinel deliberately yields none.
enabled = ["__dwellproof_no_tools__"]
mcp_call_timeout_seconds = 60

[environment]
enabled = false

[permissions]
mode = "deny"
deny = [
  "bash", "bash_output", "kill_shell", "wait", "todo_write", "complete_step",
  "read_file", "write_file", "edit_file", "multi_edit", "move_file",
  "notebook_edit", "delete_range", "delete_symbol", "ls", "glob", "grep",
  "code_index", "web_fetch", "history", "list_sessions", "read_session",
  "memory", "remember", "forget", "ask", "task", "parallel_tasks",
  "read_only_task", "run_skill", "read_skill", "read_only_skill", "install_skill",
  "explore", "research", "review", "security_review", "install_source",
  "slash_command", "connect_tool_source", "use_capability"
]

[sandbox]
bash = "enforce"
network = false

[skills]
paths = []
excluded_paths = []
disabled_skills = []

[lsp]
enabled = false

[secrets]
redact_tool_output = true
filter_subprocess_env = true
protect_sensitive_files = true
"#,
        system_prompt = toml_basic_string(SYSTEM_PROMPT)
    )
}

/// TOML basic strings escape like JSON strings.
fn toml_basic_string(value: &str) -> String {
    serde_json::to_string(value).expect("string serialization is infallible")
}

#[derive(Debug, Clone)]
pub struct ReasonixHome {
    pub root: PathBuf,
    pub workspace: PathBuf,
    pub config: PathBuf,
    pub credential_bridge: PathBuf,
    pub state: PathBuf,
    pub cache: PathBuf,
}

#[cfg(unix)]
fn set_private_dir(path: &Path) -> Result<()> {
    use std::os::unix::fs::PermissionsExt;
    fs::set_permissions(path, fs::Permissions::from_mode(0o700)).map_err(|error| {
        ReasonixError::new(
            "HOME_PREP_FAILED",
            format!("cannot restrict {}: {error}", path.display()),
        )
    })
}

#[cfg(not(unix))]
fn set_private_dir(_path: &Path) -> Result<()> {
    Ok(())
}

fn ensure_private_dir(path: &Path) -> Result<()> {
    match fs::symlink_metadata(path) {
        Ok(metadata) => {
            if !metadata.file_type().is_dir() || metadata.file_type().is_symlink() {
                return Err(ReasonixError::new(
                    "HOME_PREP_FAILED",
                    format!("Reasonix path is not a regular directory: {}", path.display()),
                ));
            }
        }
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            fs::create_dir_all(path).map_err(|error| {
                ReasonixError::new(
                    "HOME_PREP_FAILED",
                    format!("cannot create {}: {error}", path.display()),
                )
            })?;
        }
        Err(error) => {
            return Err(ReasonixError::new(
                "HOME_PREP_FAILED",
                format!("cannot inspect {}: {error}", path.display()),
            ))
        }
    }
    set_private_dir(path)
}

/// Empty the workspace so a new session never inherits prior files. The
/// workspace itself must stay the same directory inode for a running process.
pub fn reset_workspace(home: &ReasonixHome) -> Result<()> {
    let metadata = fs::symlink_metadata(&home.workspace).map_err(|error| {
        ReasonixError::new(
            "HOME_PREP_FAILED",
            format!("Reasonix workspace missing: {error}"),
        )
    })?;
    if !metadata.file_type().is_dir() || metadata.file_type().is_symlink() {
        return Err(ReasonixError::new(
            "HOME_PREP_FAILED",
            "Reasonix workspace is not a regular directory",
        ));
    }
    for entry in fs::read_dir(&home.workspace).map_err(|error| {
        ReasonixError::new(
            "HOME_PREP_FAILED",
            format!("cannot list Reasonix workspace: {error}"),
        )
    })? {
        let entry = entry.map_err(|error| {
            ReasonixError::new(
                "HOME_PREP_FAILED",
                format!("cannot read Reasonix workspace entry: {error}"),
            )
        })?;
        let path = entry.path();
        if path.is_dir() {
            fs::remove_dir_all(&path)
        } else {
            fs::remove_file(&path)
        }
        .map_err(|error| {
            ReasonixError::new(
                "HOME_PREP_FAILED",
                format!("cannot clear {}: {error}", path.display()),
            )
        })?;
    }
    Ok(())
}

fn write_private_file(path: &Path, contents: &str) -> Result<()> {
    static COUNTER: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
    let unique = COUNTER.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
    let temporary = path.with_extension(format!("tmp-{}-{unique}", std::process::id()));
    {
        use std::io::Write;
        let mut options = fs::OpenOptions::new();
        options.write(true).create_new(true);
        #[cfg(unix)]
        {
            use std::os::unix::fs::OpenOptionsExt;
            options.mode(0o600);
        }
        let mut file = options.open(&temporary).map_err(|error| {
            ReasonixError::new(
                "HOME_PREP_FAILED",
                format!("cannot write {}: {error}", temporary.display()),
            )
        })?;
        file.write_all(contents.as_bytes())
            .and_then(|()| file.sync_all())
            .map_err(|error| {
                ReasonixError::new(
                    "HOME_PREP_FAILED",
                    format!("cannot write {}: {error}", temporary.display()),
                )
            })?;
    }
    fs::rename(&temporary, path).map_err(|error| {
        ReasonixError::new(
            "HOME_PREP_FAILED",
            format!("cannot install {}: {error}", path.display()),
        )
    })?;
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(path, fs::Permissions::from_mode(0o600)).map_err(|error| {
            ReasonixError::new(
                "HOME_PREP_FAILED",
                format!("cannot restrict {}: {error}", path.display()),
            )
        })?;
    }
    Ok(())
}

/// Create or refresh the isolated home under `root` (usually the app config
/// directory) and write the pinned deny-all config.
pub fn prepare(root: &Path) -> Result<ReasonixHome> {
    if !root.is_absolute() {
        return Err(ReasonixError::new(
            "HOME_PREP_FAILED",
            "Reasonix home must be an absolute path",
        ));
    }
    ensure_private_dir(root)?;
    // Canonicalize first so platform alias paths (e.g. /var vs /private/var)
    // resolve before building the layout; the root itself must be a real
    // directory, not a symlink the caller smuggled in.
    let metadata = fs::symlink_metadata(root).map_err(|error| {
        ReasonixError::new(
            "HOME_PREP_FAILED",
            format!("cannot inspect Reasonix home: {error}"),
        )
    })?;
    if metadata.file_type().is_symlink() {
        return Err(ReasonixError::new(
            "HOME_PREP_FAILED",
            "Reasonix home must not be a symbolic link",
        ));
    }
    let resolved = root.canonicalize().map_err(|error| {
        ReasonixError::new(
            "HOME_PREP_FAILED",
            format!("cannot resolve Reasonix home: {error}"),
        )
    })?;
    let home = ReasonixHome {
        root: resolved.clone(),
        workspace: resolved.join("workspace"),
        config: resolved.join("config.toml"),
        credential_bridge: resolved.join(".env"),
        state: resolved.join("state"),
        cache: resolved.join("cache"),
    };
    let _ = fs::remove_file(&home.credential_bridge);
    ensure_private_dir(&home.workspace)?;
    reset_workspace(&home)?;
    ensure_private_dir(&home.state)?;
    ensure_private_dir(&home.cache)?;
    write_private_file(&home.config, &runtime_config())?;
    Ok(home)
}

const ENV_ALLOWLIST: &[&str] = &[
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "PATH",
    "SSL_CERT_DIR",
    "SSL_CERT_FILE",
    "SystemRoot",
    "TEMP",
    "TMP",
    "TMPDIR",
    "WINDIR",
];

/// Environment for the ACP child: allowlisted pass-through plus the isolated
/// home locations. Nothing else leaks into the runtime.
pub fn process_env(home: &ReasonixHome) -> Vec<(String, String)> {
    let mut env: Vec<(String, String)> = Vec::new();
    for name in ENV_ALLOWLIST {
        if let Ok(value) = std::env::var(name) {
            env.push((name.to_string(), value));
        }
    }
    if !env.iter().any(|(name, _)| name == "PATH") {
        env.push((
            "PATH".to_string(),
            "/usr/bin:/bin:/usr/sbin:/sbin".to_string(),
        ));
    }
    env.push(("REASONIX_HOME".to_string(), home.root.display().to_string()));
    env.push((
        "REASONIX_STATE_HOME".to_string(),
        home.state.display().to_string(),
    ));
    env.push((
        "REASONIX_CACHE_HOME".to_string(),
        home.cache.display().to_string(),
    ));
    env.push((
        "REASONIX_CREDENTIALS_STORE".to_string(),
        "file".to_string(),
    ));
    env
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn prepare_creates_private_layout_and_config() {
        let root = std::env::temp_dir().join(format!("dwellproof-home-{}", std::process::id()));
        let home = prepare(&root).expect("prepare home");
        assert!(home.workspace.is_dir());
        assert!(home.state.is_dir());
        assert!(home.cache.is_dir());
        let config = fs::read_to_string(&home.config).expect("read config");
        assert!(config.contains("__dwellproof_no_tools__"));
        assert!(config.contains("api.deepseek.com"));
        assert!(config.contains("mode = \"deny\""));
        assert!(config.contains("network = false"));

        fs::write(home.workspace.join("stale.txt"), b"x").expect("write stale file");
        reset_workspace(&home).expect("reset workspace");
        assert!(fs::read_dir(&home.workspace).unwrap().next().is_none());

        fs::remove_dir_all(&root).expect("cleanup");
    }

    #[test]
    fn prepare_rejects_relative_root() {
        let error = prepare(Path::new("relative/path")).unwrap_err();
        assert_eq!(error.code, "HOME_PREP_FAILED");
    }

    #[test]
    fn process_env_filters_host_variables() {
        let root = std::env::temp_dir().join(format!("dwellproof-env-{}", std::process::id()));
        let home = prepare(&root).expect("prepare home");
        let env = process_env(&home);
        assert!(env.iter().any(|(name, _)| name == "REASONIX_HOME"));
        assert!(!env.iter().any(|(name, _)| name == "DEEPSEEK_API_KEY"));
        assert!(!env.iter().any(|(name, _)| name == "HOME"));
        fs::remove_dir_all(&root).expect("cleanup");
    }
}

//! DeepSeek credential resolution and the short-lived `.env` bridge.
//!
//! Upstream Reasonix v1.17.11 only reads the provider key from
//! `REASONIX_HOME/.env`, so the key is bridged there for the lifetime of a
//! `session/new` / `session/load` request with 0600 permissions and removed
//! immediately afterwards. The key itself comes from the host process
//! environment and is never persisted by DwellProof.

use super::home::ReasonixHome;
use super::{ReasonixError, Result};
use std::fs;
use std::io::Write;

pub fn resolve_api_key() -> Result<String> {
    let key = std::env::var("DEEPSEEK_API_KEY").map_err(|_| {
        ReasonixError::new(
            "SETUP_REQUIRED",
            "DEEPSEEK_API_KEY is not set in the DwellProof process environment",
        )
    })?;
    let key = key.trim().to_string();
    if key.is_empty() || key.contains(['\r', '\n', '\0']) {
        return Err(ReasonixError::new(
            "SETUP_REQUIRED",
            "DEEPSEEK_API_KEY is empty or malformed",
        ));
    }
    Ok(key)
}

/// RAII guard for the credential bridge file; creation is exclusive and the
/// file is removed when the guard drops, including on panic paths.
pub struct CredentialBridge {
    path: std::path::PathBuf,
}

impl CredentialBridge {
    pub fn create(home: &ReasonixHome, key: &str) -> Result<Self> {
        let _ = fs::remove_file(&home.credential_bridge);
        {
            let mut options = fs::OpenOptions::new();
            options.write(true).create_new(true);
            #[cfg(unix)]
            {
                use std::os::unix::fs::OpenOptionsExt;
                options.mode(0o600);
            }
            let mut file = options.open(&home.credential_bridge).map_err(|error| {
                ReasonixError::new(
                    "CREDENTIAL_BRIDGE_FAILED",
                    format!("cannot create credential bridge: {error}"),
                )
            })?;
            let quoted = serde_json::to_string(key).expect("string serialization is infallible");
            file.write_all(format!("DEEPSEEK_API_KEY={quoted}\n").as_bytes())
                .and_then(|()| file.sync_all())
                .map_err(|error| {
                    ReasonixError::new(
                        "CREDENTIAL_BRIDGE_FAILED",
                        format!("cannot write credential bridge: {error}"),
                    )
                })?;
        }
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            fs::set_permissions(&home.credential_bridge, fs::Permissions::from_mode(0o600))
                .map_err(|error| {
                    ReasonixError::new(
                        "CREDENTIAL_BRIDGE_FAILED",
                        format!("cannot restrict credential bridge: {error}"),
                    )
                })?;
        }
        Ok(Self {
            path: home.credential_bridge.clone(),
        })
    }
}

impl Drop for CredentialBridge {
    fn drop(&mut self) {
        let _ = fs::remove_file(&self.path);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::reasonix::home;

    #[test]
    fn bridge_writes_and_removes_file() {
        let root = std::env::temp_dir().join(format!("dwellproof-cred-{}", std::process::id()));
        let layout = home::prepare(&root).expect("prepare home");
        let bridge_path = layout.credential_bridge.clone();
        {
            let _bridge = CredentialBridge::create(&layout, "sk-test-key").expect("create bridge");
            let contents = fs::read_to_string(&bridge_path).expect("read bridge");
            assert_eq!(contents, "DEEPSEEK_API_KEY=\"sk-test-key\"\n");
            #[cfg(unix)]
            {
                use std::os::unix::fs::PermissionsExt;
                let mode = fs::metadata(&bridge_path).unwrap().permissions().mode();
                assert_eq!(mode & 0o777, 0o600);
            }
        }
        assert!(!bridge_path.exists());
        fs::remove_dir_all(&root).expect("cleanup");
    }
}

//! Append-only audit log for Reasonix activity. Only hashes and identifiers
//! are recorded — never prompt or response content.

use super::{ReasonixError, Result};
use serde::Serialize;
use sha2::{Digest, Sha256};
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};

#[derive(Debug, Serialize)]
pub struct AuditEntry {
    pub timestamp: String,
    pub event: String,
    pub case_id: String,
    pub session_id: Option<String>,
    pub prompt_sha256: Option<String>,
    pub response_sha256: Option<String>,
    pub outcome: String,
}

pub fn sha256_hex(contents: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(contents.as_bytes());
    hex::encode(hasher.finalize())
}

fn timestamp_now() -> String {
    // Compact UTC timestamp without pulling in a date crate.
    let secs = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|duration| duration.as_secs())
        .unwrap_or(0);
    let days = secs / 86_400;
    let day_secs = secs % 86_400;
    let (year, month, day) = civil_from_days(days);
    format!(
        "{year:04}-{month:02}-{day:02}T{:02}:{:02}:{:02}Z",
        day_secs / 3600,
        (day_secs % 3600) / 60,
        day_secs % 60
    )
}

// Howard Hinnant's civil-from-days algorithm.
fn civil_from_days(days: u64) -> (u64, u64, u64) {
    let z = days + 719_468;
    let era = z / 146_097;
    let doe = z % 146_097;
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365;
    let year = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let day = doy - (153 * mp + 2) / 5 + 1;
    let month = if mp < 10 { mp + 3 } else { mp - 9 };
    (if month <= 2 { year + 1 } else { year }, month, day)
}

pub struct AuditLog {
    path: PathBuf,
}

impl AuditLog {
    pub fn new(app_data_dir: &Path) -> Result<Self> {
        fs::create_dir_all(app_data_dir).map_err(|error| {
            ReasonixError::new(
                "AUDIT_FAILED",
                format!("cannot create audit directory: {error}"),
            )
        })?;
        Ok(Self {
            path: app_data_dir.join("reasonix-audit.jsonl"),
        })
    }

    pub fn record(&self, entry: &AuditEntry) -> Result<()> {
        let mut line = serde_json::to_string(entry)
            .map_err(|error| ReasonixError::new("AUDIT_FAILED", error.to_string()))?;
        line.push('\n');
        let mut file = fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&self.path)
            .map_err(|error| {
                ReasonixError::new(
                    "AUDIT_FAILED",
                    format!("cannot open audit log {}: {error}", self.path.display()),
                )
            })?;
        file.write_all(line.as_bytes()).map_err(|error| {
            ReasonixError::new(
                "AUDIT_FAILED",
                format!("cannot append audit log: {error}"),
            )
        })?;
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            let _ = fs::set_permissions(&self.path, fs::Permissions::from_mode(0o600));
        }
        Ok(())
    }

    pub fn record_event(
        &self,
        event: &str,
        case_id: &str,
        session_id: Option<&str>,
        prompt: Option<&str>,
        response: Option<&str>,
        outcome: &str,
    ) -> Result<()> {
        self.record(&AuditEntry {
            timestamp: timestamp_now(),
            event: event.to_string(),
            case_id: case_id.to_string(),
            session_id: session_id.map(str::to_string),
            prompt_sha256: prompt.map(sha256_hex),
            response_sha256: response.map(sha256_hex),
            outcome: outcome.to_string(),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn audit_records_hashes_not_content() {
        let dir = std::env::temp_dir().join(format!("dwellproof-audit-{}", std::process::id()));
        let log = AuditLog::new(&dir).expect("create audit log");
        log.record_event(
            "explain",
            "GZ-DEMO-001",
            Some("session-1"),
            Some("secret question text"),
            Some("secret answer text"),
            "ok",
        )
        .expect("record event");
        let contents = fs::read_to_string(dir.join("reasonix-audit.jsonl")).expect("read log");
        assert!(contents.contains("GZ-DEMO-001"));
        assert!(contents.contains("session-1"));
        assert!(!contents.contains("secret question text"));
        assert!(!contents.contains("secret answer text"));
        fs::remove_dir_all(&dir).expect("cleanup");
    }

    #[test]
    fn civil_from_days_matches_known_dates() {
        assert_eq!(civil_from_days(0), (1970, 1, 1));
        assert_eq!(civil_from_days(19_723), (2024, 1, 1));
        assert_eq!(civil_from_days(20_454), (2026, 1, 1));
        assert_eq!(civil_from_days(20_475), (2026, 1, 22));
    }
}

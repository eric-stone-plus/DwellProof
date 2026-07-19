//! Reasonix shadow-mode integration for the DwellProof desktop shell.
//!
//! Reasonix runs as an isolated ACP child process with a pinned, SHA-256
//! verified binary. It may explain evidence gaps and answer case questions
//! with citations, but it has no tools, no write access, and no authority
//! over evidence state, readiness, or calculations. See
//! `docs/decisions/ADR-0001-REASONIX-BOUNDARY.md`.

pub mod acp;
pub mod audit;
pub mod credentials;
pub mod home;
pub mod manifest;
pub mod policy;

use serde::Serialize;

/// Structured error surfaced to the frontend; `code` is stable for UI logic.
#[derive(Debug, Clone, Serialize)]
pub struct ReasonixError {
    pub code: String,
    pub message: String,
}

impl ReasonixError {
    pub fn new(code: &str, message: impl Into<String>) -> Self {
        Self {
            code: code.to_string(),
            message: message.into(),
        }
    }
}

impl std::fmt::Display for ReasonixError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}: {}", self.code, self.message)
    }
}

impl std::error::Error for ReasonixError {}

pub type Result<T> = std::result::Result<T, ReasonixError>;

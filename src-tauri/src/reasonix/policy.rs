//! Output policy: caps and citation validation for Reasonix responses.
//!
//! A response that never references a known gate or source identifier cannot
//! be grounded in the case snapshot, so it fails closed: the caller shows a
//! refusal card instead of the generated text.

/// Stable identifiers a grounded answer may cite.
pub const KNOWN_CITATION_IDS: &[&str] = &[
    "G01", "G02", "G03", "G04", "G05", "G06", "G07",
    "deed-tax", "nbs-index", "lpr",
];

pub const MAX_QUESTION_CHARS: usize = 4_000;
pub const MAX_SNAPSHOT_CHARS: usize = 32_000;
pub const MAX_FRAME_BYTES: usize = 1024 * 1024;

/// True when the response cites at least one known identifier.
pub fn has_citation(text: &str) -> bool {
    KNOWN_CITATION_IDS.iter().any(|id| text.contains(id))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn citation_check_accepts_gate_and_source_ids() {
        assert!(has_citation("产权人与处分权（G01）仍缺登记证明。"));
        assert!(has_citation("LPR 只是基准，见 lpr 来源边界。"));
        assert!(has_citation("契税优惠见 deed-tax 快照。"));
    }

    #[test]
    fn citation_check_rejects_ungrounded_text() {
        assert!(!has_citation("这套房子看起来不错，可以买入。"));
        assert!(!has_citation(""));
    }
}

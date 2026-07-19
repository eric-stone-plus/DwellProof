//! Pinned Reasonix release manifest and pre-launch binary verification.
//!
//! Values must stay in sync with `scripts/fetch_reasonix_runtime.py`. The
//! binary is verified before every launch; a mismatch or an unexpected file
//! shape fails closed.

use super::{ReasonixError, Result};
use sha2::{Digest, Sha256};
use std::fs;
use std::io::Read;
use std::path::{Path, PathBuf};

pub const UPSTREAM: &str = "esengine/DeepSeek-Reasonix";
pub const PINNED_VERSION: &str = "1.17.11";
pub const PINNED_COMMIT: &str = "20a64b4d15687fbddb7ccc658daf909f71d01427";
pub const PROTOCOL_VERSION: u64 = 1;

#[cfg(all(target_os = "macos", target_arch = "x86_64"))]
pub const BINARY_SHA256: &str = "f839fcc1b85539eb2bd8c921239c72570a02b8f38eec23d51b1987148c349adc";
#[cfg(all(target_os = "macos", target_arch = "aarch64"))]
pub const BINARY_SHA256: &str = "a7adba9ee65175e73a4218b2ffb78a3c09e81c5a47b59d6ceb153ba3bdab1ff6";
#[cfg(all(target_os = "linux", target_arch = "x86_64"))]
pub const BINARY_SHA256: &str = "65b1de073d7c4c6fb4d2a6b009e42987e2f7d3e300ba9a496f57966285d8b0c3";

#[cfg(not(any(
    all(target_os = "macos", target_arch = "x86_64"),
    all(target_os = "macos", target_arch = "aarch64"),
    all(target_os = "linux", target_arch = "x86_64"),
)))]
pub const BINARY_SHA256: &str = "";

pub fn platform_key() -> &'static str {
    #[cfg(all(target_os = "macos", target_arch = "x86_64"))]
    return "darwin-x64";
    #[cfg(all(target_os = "macos", target_arch = "aarch64"))]
    return "darwin-arm64";
    #[cfg(all(target_os = "linux", target_arch = "x86_64"))]
    return "linux-x64";
    #[cfg(not(any(
        all(target_os = "macos", target_arch = "x86_64"),
        all(target_os = "macos", target_arch = "aarch64"),
        all(target_os = "linux", target_arch = "x86_64"),
    )))]
    return "unsupported";
}

pub fn sha256_file(path: &Path) -> Result<String> {
    let mut file = fs::File::open(path).map_err(|error| {
        ReasonixError::new(
            "BINARY_VERIFY_FAILED",
            format!("cannot open Reasonix binary {}: {error}", path.display()),
        )
    })?;
    let mut hasher = Sha256::new();
    let mut buffer = [0u8; 64 * 1024];
    loop {
        let read = file.read(&mut buffer).map_err(|error| {
            ReasonixError::new(
                "BINARY_VERIFY_FAILED",
                format!("cannot read Reasonix binary {}: {error}", path.display()),
            )
        })?;
        if read == 0 {
            break;
        }
        hasher.update(&buffer[..read]);
    }
    Ok(hex::encode(hasher.finalize()))
}

/// Verify that `path` is the exact pinned Reasonix binary: expected file
/// name, regular non-symlink file, executable on Unix, and matching SHA-256.
pub fn verify_binary(path: &Path) -> Result<()> {
    if BINARY_SHA256.is_empty() {
        return Err(ReasonixError::new(
            "UNSUPPORTED_PLATFORM",
            format!("no pinned Reasonix binary for {}", platform_key()),
        ));
    }
    if path.file_name().and_then(|name| name.to_str()) != Some("reasonix") {
        return Err(ReasonixError::new(
            "BINARY_VERIFY_FAILED",
            format!("unexpected Reasonix binary name: {}", path.display()),
        ));
    }
    let metadata = fs::symlink_metadata(path).map_err(|error| {
        ReasonixError::new(
            "BINARY_NOT_FOUND",
            format!("Reasonix binary not found at {}: {error}", path.display()),
        )
    })?;
    if !metadata.file_type().is_file() || metadata.file_type().is_symlink() {
        return Err(ReasonixError::new(
            "BINARY_VERIFY_FAILED",
            format!("Reasonix binary is not a regular file: {}", path.display()),
        ));
    }
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        if metadata.permissions().mode() & 0o111 == 0 {
            return Err(ReasonixError::new(
                "BINARY_VERIFY_FAILED",
                format!("Reasonix binary is not executable: {}", path.display()),
            ));
        }
    }
    let digest = sha256_file(path)?;
    if digest != BINARY_SHA256 {
        return Err(ReasonixError::new(
            "BINARY_VERIFY_FAILED",
            format!(
                "Reasonix binary SHA-256 mismatch at {}: got {digest}, expected {BINARY_SHA256}",
                path.display()
            ),
        ));
    }
    Ok(())
}

/// Locate the Reasonix binary: explicit override first, then the packaged
/// app Resources directory, then the development `.runtime` cache.
pub fn resolve_binary_path() -> Result<PathBuf> {
    if let Ok(override_path) = std::env::var("DWELLPROOF_REASONIX_BINARY") {
        let path = PathBuf::from(override_path);
        verify_binary(&path)?;
        return Ok(path);
    }

    let mut candidates: Vec<PathBuf> = Vec::new();
    if let Ok(exe) = std::env::current_exe() {
        if let Some(macos_dir) = exe.parent() {
            candidates.push(macos_dir.join("../Resources/reasonix"));
        }
    }
    if let Ok(manifest_dir) = std::env::var("CARGO_MANIFEST_DIR") {
        candidates.push(PathBuf::from(manifest_dir).join(format!(
            "../desktop/.runtime/reasonix-v{PINNED_VERSION}-{}/reasonix",
            platform_key()
        )));
    }
    candidates.push(PathBuf::from(format!(
        "desktop/.runtime/reasonix-v{PINNED_VERSION}-{}/reasonix",
        platform_key()
    )));

    for candidate in &candidates {
        let normalized = candidate.canonicalize().unwrap_or_else(|_| candidate.clone());
        if normalized.exists() {
            verify_binary(&normalized)?;
            return Ok(normalized);
        }
    }
    Err(ReasonixError::new(
        "BINARY_NOT_FOUND",
        format!(
            "pinned {UPSTREAM} v{PINNED_VERSION} (commit {PINNED_COMMIT}) binary not found; \
             run scripts/fetch_reasonix_runtime.py"
        ),
    ))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;

    #[test]
    fn sha256_file_matches_known_digest() {
        let mut path = std::env::temp_dir();
        path.push(format!("dwellproof-sha-test-{}", std::process::id()));
        {
            let mut file = fs::File::create(&path).expect("create temp file");
            file.write_all(b"abc").expect("write temp file");
        }
        let digest = sha256_file(&path).expect("digest");
        let _ = fs::remove_file(&path);
        assert_eq!(
            digest,
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        );
    }

    #[test]
    fn verify_binary_rejects_missing_file() {
        let error = verify_binary(Path::new("/definitely/not/reasonix")).unwrap_err();
        assert!(
            error.code == "BINARY_NOT_FOUND" || error.code == "BINARY_VERIFY_FAILED",
            "unexpected code {}",
            error.code
        );
    }

    #[test]
    fn verify_binary_rejects_wrong_name() {
        let mut path = std::env::temp_dir();
        path.push(format!("dwellproof-name-test-{}", std::process::id()));
        fs::write(&path, b"x").expect("write temp file");
        let error = verify_binary(&path).unwrap_err();
        let _ = fs::remove_file(&path);
        assert!(
            error.code == "BINARY_VERIFY_FAILED" || error.code == "UNSUPPORTED_PLATFORM",
            "unexpected code {}",
            error.code
        );
    }
}

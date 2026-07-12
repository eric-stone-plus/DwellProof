# DwellProof desktop

The desktop application uses Tauri 2 and the operating system WebView. It embeds
the static Next.js export from `web/out/`; it does not bundle Chromium, start a
localhost service, or include Node.js.

Build a local macOS test distribution from the repository root:

```sh
./desktop/build_macos.sh
```

Expected outputs are under `desktop/dist/`: an ad-hoc-signed `.app`, a simple
`.dmg`, `SHA256SUMS`, and `BUILD-INFO.txt`. They are ignored by Git because they
are generated artifacts. Rust intermediates remain under `src-tauri/target/`.

The current build is a presentation shell. It does not yet execute the Python
accuracy core. That future boundary must use a fixed JSON protocol and a bundled,
restricted sidecar; the WebView must never receive generic shell or filesystem
permissions. The current WebView has no Tauri IPC permissions at all.

External official-source links work in a normal browser. The current desktop
shell intentionally does not grant an opener permission, so it may refuse those
links rather than load remote pages into a privileged WebView. A future desktop
opener must use an explicit official-domain allowlist.

Local ad-hoc signing is suitable only for testing on this Mac. Public
distribution requires a valid Apple Developer ID, hardened runtime, notarization,
stapling, and separately verified x86_64/arm64 builds.

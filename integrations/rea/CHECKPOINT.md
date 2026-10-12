# REA isolated integration checkpoint

Status: PREPARED — not installed or runtime-tested.

Upstream: https://github.com/morluto/rea
Official README and docs/installation.md reviewed 2026-10-12.

Safety:
- Keep main unchanged.
- Do not alter generate_voices_by_chars.py or any 068 voice settings.
- Do not modify generated audio/video assets.
- REA is a diagnostic tool, not a video rendering engine.
- Node requirement: 22.19+, 24.11+, or 26+.
- npm setup is interactive and modifies agent configuration; avoid unattended setup in CI.
- For isolated CLI investigation, use official npx -y rea-agents@latest analyze-javascript-application /absolute/path/to/app --json on a valid extracted JS/Electron target.
- Do not analyze the Python voice script with the JavaScript analyzer.
- No valid target directory, voice script path, or checkpoint has yet been confirmed in this repository.

Next: locate the actual 068 script and project checkpoints (possibly elsewhere); identify a valid JS/Electron target; test REA in an isolated environment; verify unchanged voice outputs.

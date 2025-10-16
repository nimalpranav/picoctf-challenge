# Simple File Viewer — LFI / Path Traversal Challenge

Category: Web — LFI / Path traversal
Difficulty: Easy (suggested 50 pts)
Learning goal: teach traversal bypasses (percent-encoding, dot tricks)

## Files
- app.py        — Flask app (reads FLAG from env var)
- Dockerfile
- docker-compose.yml
- exploit_test.py — demonstrates intended solve + negative tests
- notes.md      — environment-specific notes

## Run locally (reviewer)
1. Build & run:
   docker compose up --build
2. Visit: http://localhost:5000
3. Test cases:
   - /view?file=flag.txt → Access denied.
   - /view?file=....//app/flag.txt → returns flag.
   - /robots.txt → robots content.

## How we protect host
- Container writes flag inside container; no host volumes.
- Dev server only for CTF testing; recommend running under a per-team container.

## Intended fix (learning)
Use path canonicalization + allowlist and avoid returning arbitrary file contents.

## Notes
- This challenge intentionally blocks trivial direct reads (flag.txt) but allows traversal bypass. See notes.md for OS-specific details.

# Sync Labs adapter HTTP verification

2026-10-26: reuse `sync.sim.yaml` and `default.js`; fixture sources and startup
commands are in README.md. No provider mock or paid service is contacted.

`VPT_SYNC_SIM_URL=http://127.0.0.1:4907/sync .venv/bin/python -m pytest -q tests/test_sync_labs.py`
from server/ runs the real Requests client and FFmpeg against the simulation.
The redirect regression reproduced `GET HTTP 302: non-JSON response` before
the fix, then downloaded and published valid video after following the relative
Location. The simulation log showed GET /redirect.mp4 (302), then GET
/output.mp4 (200), both without x-api-key. Mock handlers reject credential leaks.
Tests also model redirect loops, missing Location and invalid target schemes.
This verifies local transport behavior, not Sync Labs model quality or the
user's actual CDN response. Local listening and client TCP require sandbox approval.

2026-10-28: progress regression now requests `include=progress` and the fixture
returns `progress_percent=41.5` during processing. fal also models `logs=true`,
queue position and runner logs; HeyGen retains status-only progress. Attempted
`postman simulation run .../sync.sim.yaml --port 4907 --output ndjson --no-history`
in Work Mode; startup failed with `listen EPERM 127.0.0.1`, so no HTTP calls were
served and no new real-HTTP pass is claimed. Rerun the documented simulations and
progress callback tests in an ordinary terminal. Local deterministic polling tests
verify query arguments, callback payloads, redaction and no premature completion;
these do not establish actual cloud availability or account-specific fields.

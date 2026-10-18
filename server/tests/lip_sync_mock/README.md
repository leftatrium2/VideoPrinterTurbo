# Sync Labs local HTTP verification

Contract sources (checked 2026-10-17):

- https://sync.so/docs/developer-guides/asset-uploads
- https://sync.so/docs/api-reference/api/generate-api/create
- https://sync.so/docs/api-reference/api/generate-api/get
- https://sync.so/docs/developer-guides/sync-mode

This hand-written fixture models only the adapter's calls. It validates content type,
file size, registered assets, authentication boundaries, idempotency header and sync
mode. It does not run a lip-sync model. Owner-mock discovery was skipped; the fixture
is based on the official contract, not a provider-maintained mock.

From the repository root, start:

```sh
postman simulation run server/tests/lip_sync_mock/sync.sim.yaml --port 4907 --output ndjson --no-history
```

In another terminal:

```sh
cd server
VPT_SYNC_SIM_URL=http://127.0.0.1:4907/sync .venv/bin/python -m pytest -q tests/test_sync_labs.py
```

Stop the simulation with Ctrl-C. No real service, account, key, or paid generation is used.

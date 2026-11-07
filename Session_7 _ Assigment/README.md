# Session 7: Custodial Transaction Service

Endpoints (http://127.0.0.1:8000/docs)
- GET  /status        service account, balance, chain id, current message
- POST /encode        ABI-encoded setMessage call (selector check)
- POST /prepare       unsigned tx preview
- POST /send          sign + submit + wait for receipt, writes audit record
- GET  /tx/{hash}     confirmation tracking (pending/confirmed/reverted + confirmations)
- GET  /audit         last audit records (backend/audit_log.jsonl)

Requirements checklist
- Key from .env only; only the public address is ever printed.
- Nonce: lock + local counter, so parallel /send calls get 0,1,2...; a failed send releases its nonce.
- Errors: 400 simulation_failed, 502 rejected_by_node, 504 timeout (with hash), 422 reverted.
- Audit: request_id, request, nonce, tx_hash, outcome, block, gas, timestamp.
- .gitignore excludes .env, .venv and audit_log.jsonl.

Run (Mac):
  cd session7-custodial-service/backend
  python3 -m venv .venv && source .venv/bin/activate
  pip install -r ../requirements.txt
  cp .env.example .env      # then fill in values
  uvicorn main:app --reload

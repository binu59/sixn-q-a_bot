# Meridian governance assistant

Plain-English Q&A over `data/entities.json`, answering only from what the selected user may see.

## Run
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env        # add OPENAI_API_KEY (never committed)
    uvicorn app.main:app        # open http://127.0.0.1:8000
    python -m pytest -q         # offline proof of the access rules
    python scripts/transcripts.py   # live transcripts -> TRANSCRIPTS.md

## Approach
Authorisation happens in code, before the model. The request carries only a `user_id`; the server looks up the
scope in users.json, filters entities, replaces `bank_account` / `treasury_balance_usd` with a restricted marker, and
sends only that to the LLM. What the model never receives it cannot leak, so the prompt is not the security boundary.
Layers: (1) scope filter, (2) redaction, (3) instruction-like text in data is withheld, (4) a prompt telling the model to
treat data as untrusted, (5) an output guard that swaps any answer containing hidden identifiers or sensitive values for
the standard not-found reply.

## Decisions
- **Out-of-scope = not-found:** no special-casing. A hidden entity and a made-up one produce byte-identical model
  context, so there is nothing to distinguish (test: `test_out_of_scope_and_nonexistent_take_identical_path`).
- **Scope by `region` field, not by name:** "Europa Freight Lanka" is Asia Pacific; "Pacific Rim Logistics (Europe) B.V." is Europe.
- **Treasury aggregates:** computed in code via a tool call, whole-scope only, min 3 entities, count only at 2,000,000. See CONFLICTS.md.
- **Average** includes dormant zero-balance entities, rounded to the nearest USD.
- **Rule 3 applies to everyone**, including Corporate Planning, despite `clearance: elevated`.
- **Scope is per user record, not per person:** Siti is also a director of ap-007, but the Point of Contact only sees ap-004.
- Person names appear only via in-scope records (e.g. Marcus Tan also directs a Middle East entity; a regional user never learns that).

## Noticed
- `ap-005` notes contain a prompt injection. Withheld before the model sees it; the data should be cleaned at source.
- The user switcher is not authentication; production would take identity from SSO/session.
- The output guard only catches exact strings (names, IDs, IBANs, formatted balances); it is a backstop, not the boundary.
- Model output is not deterministic; tests prove what the model receives, and `TRANSCRIPTS.md` shows live behaviour.
- Short-name matching is model-dependent: "Meridian Vietnam" sometimes returns not-found, while the full name ("Meridian Vietnam Company Limited") or the id (ap-005) works reliably. This errs on the side of under-answering, never over-sharing. With more time I'd add deterministic fuzzy name matching in code, restricted to in-scope entities, to resolve the name before the model is called.

## With more time
- Real authn, audit log of questions asked, rate limiting (repeated aggregate queries).
- Adversarial eval set run against the live model in CI; fuzzier leak detection (e.g. "4.18 million").
- Structured retrieval for larger registers instead of putting all in-scope records in context.
- Fix the source data (injection) and have the owner decide on single-entity treasury access.
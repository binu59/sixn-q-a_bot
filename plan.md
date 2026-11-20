# PLAN

## What I'm building
A small Q&A assistant over Meridian Group's governance data (data/entities.json).
The user picks one of four users in a one-page UI, asks a question in plain English,
and gets an answer grounded only in records that user is allowed to see.

## Approach (core idea)
Authorization happens in code, before the LLM. The user's scope is looked up from
users.json (never from the question), entities are filtered server-side, sensitive
fields are stripped, and only the filtered data reaches the model. The model cannot
leak what it never receives.

## Assumptions
- Scope is derived solely from the user record: region, entity, or all.
- Out-of-scope and non-existent entities get the same response.
- bank_account and treasury_balance_usd are redacted for every role. The assistant
  says the value exists but is access-restricted (only for in-scope entities).
- If something in the brief is ambiguous, I decide, log it in the README, and move on.
- The treasury request (docs/requests/treasury-2026-07.md) may conflict with the
  sensitive-field rule. I'll flag it in CONFLICTS.md and choose the safest delivery.

## Deliberately leaving out
- Real authentication (the user switcher is a stand-in).
- Styling, streaming, chat history, persistence.
- Vector search or RAG (24 entities fit in context after filtering).

## Verification
Automated tests that run the same attack questions as all four users and assert
no out-of-scope entity name, bank account or balance appears in any response.
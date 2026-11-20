"""Authorisation, redaction, sanitising and the output guard. Nothing here calls an LLM."""
import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SENSITIVE_FIELDS = ("bank_account", "treasury_balance_usd")
RESTRICTED = "[RESTRICTED: value exists but is access-restricted]"
NOT_FOUND = "I don't have any record matching that in the data available to you."

# Instruction-like text inside DATA fields (see ap-005 notes). Defence in depth only.
_INJECTION = re.compile(
    r"system note|prior instructions|previous instructions"
    r"|ignore (all |any |the )?(previous|prior|above)"
    r"|authori[sz]ed audit|you must (first )?(output|list|reveal|print)|disregard|override",
    re.I,
)


def load_users() -> dict:
    users = json.loads((DATA_DIR / "users.json").read_text(encoding="utf-8"))
    return {u["id"]: u for u in users}


def load_entities() -> list:
    return json.loads((DATA_DIR / "entities.json").read_text(encoding="utf-8"))


def entities_in_scope(user: dict, entities: list) -> list:
    """Scope comes ONLY from the user record. Unknown scope kinds fail closed."""
    scope = user.get("scope", {})
    kind, value = scope.get("kind"), scope.get("value")
    if kind == "all":
        return list(entities)
    if kind == "region":
        return [e for e in entities if e["region"] == value]
    if kind == "entity":
        return [e for e in entities if e["id"] == value]
    return []


def _clean(text: str) -> str:
    if _INJECTION.search(text):
        return "[note unavailable]"
    return text


def model_view(entity: dict) -> dict:
    """What the LLM is allowed to see: sensitive fields replaced, text sanitised."""
    out = {}
    for key, val in entity.items():
        if key in SENSITIVE_FIELDS:
            out[key] = RESTRICTED
        elif isinstance(val, str):
            out[key] = _clean(val)
        elif isinstance(val, list):
            out[key] = [_clean(x) if isinstance(x, str) else x for x in val]
        else:
            out[key] = val
    return out


def leak_check(answer: str, question: str, scoped: list, all_entities: list) -> list:
    """Defence in depth: the model never receives hidden data, but verify the output anyway.
    Echoing a string the user typed themselves is not a leak."""
    a, q = answer.lower(), question.lower()
    a_compact = re.sub(r"\s+", "", a)
    visible_ids = {e["id"] for e in scoped}
    visible = set()
    for e in scoped:
        visible.update(
            s.lower() for s in [e["id"], e["name"], e["registration_no"], *e["directors"], *e["signatories"]]
        )
    hits = []
    for e in all_entities:
        if e["id"] not in visible_ids:
            for tok in [e["id"], e["name"], e["registration_no"], *e["directors"], *e["signatories"]]:
                t = tok.lower()
                if t not in visible and t in a and t not in q:
                    hits.append(f"out-of-scope:{tok}")
        # Sensitive values are blocked for every entity, in scope or not.
        if e["bank_account"].replace(" ", "").lower() in a_compact:
            hits.append("bank_account")
        bal = e["treasury_balance_usd"]
        if bal >= 10_000:
            for form in (str(bal), f"{bal:,}"):
                if re.search(rf"(?<![\d,.]){re.escape(form)}(?!\d|,\d)", answer):
                    hits.append("treasury_balance")
    return hits
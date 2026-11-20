"""Treasury aggregates (TR-2026-07). Computed in code, never by the model.

Policy (see CONFLICTS.md #1):
- Only over the user's whole scope. No sub-set filters, so no differencing.
- Refused when fewer than MIN_GROUP entities are in scope: over one entity the
  total/average IS the restricted balance.
- count_above only at the funding trigger; arbitrary thresholds would let a user
  probe the distribution of balances.
"""
MIN_GROUP = 3
FUNDING_TRIGGER = 2_000_000


def treasury_aggregate(scoped: list, metric: str, threshold_usd=None) -> dict:
    n = len(scoped)
    if n < MIN_GROUP:
        return {
            "status": "restricted",
            "reason": "Treasury totals are not available at your access level: a figure over "
            "so few entities would disclose an individual restricted balance.",
        }
    balances = [e["treasury_balance_usd"] for e in scoped]
    base = {"status": "ok", "metric": metric, "currency": "USD",
            "entities_counted": n, "entity_ids": [e["id"] for e in scoped]}
    if metric == "total":
        return {**base, "value": sum(balances)}
    if metric == "average":
        return {**base, "value": round(sum(balances) / n), "note": "mean over all entities counted, rounded to nearest USD"}
    if metric == "count_above":
        if threshold_usd != FUNDING_TRIGGER:
            return {"status": "unsupported_threshold",
                    "reason": f"Only the standard intercompany funding trigger ({FUNDING_TRIGGER:,} USD) is supported."}
        return {**base, "value": sum(b > FUNDING_TRIGGER for b in balances), "threshold_usd": FUNDING_TRIGGER}
    return {"status": "error", "reason": "unknown metric"}
# CONFLICTS

1. **Treasury totals (TR-2026-07) vs. "balances must not appear" and scope.**
Over one entity, a total or average *is* that entity's balance, and "count above 2M" reveals it by range. This hits the Cold Chain Point of Contact (one entity), the exact account Meera asked to include. Arbitrary thresholds would also let users probe the balances. Done: totals/average/count are computed in code (never by the model) for scopes of 3+ entities (both directors, Corporate Planning); refused for the single-entity user; count only at the 2,000,000 trigger; no sub-set filters. Needs the owner's decision before the pilot gets figures.

2. **Corporate Planning "elevated" clearance vs. rule 3.**
users.json implies Corporate Planning may see more; the brief says sensitive fields never appear. Rule 3 wins: nobody, including Corporate Planning, gets per-entity balances or bank accounts.

3. **"Never state a number not in the data" vs. derived totals.**
Totals aren't in the data. Resolved by computing them deterministically from in-scope records and citing those entities.
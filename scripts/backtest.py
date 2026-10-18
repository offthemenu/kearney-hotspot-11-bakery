"""Honest backtest: score with 2021->2022 data only (same filters as today), then see who actually rose by 2025Q3-2026Q2."""
import json, pandas as pd
from analyze import score, sel, Q

early = score(Q[:4], Q[4:8])                       # signal as of end-2022
now = Q[-4:]
w = lambda qs: sel[sel.q.isin(qs)].groupby('k')
outcome = pd.DataFrame({
    'sales_g': (w(now).THSMON_SELNG_AMT.sum() / 4) / early.sales_now - 1,
    'wk_shift': w(now).WKEND_SELNG_AMT.sum() / w(now).THSMON_SELNG_AMT.sum()
                - sel[sel.q.isin(Q[4:8])].groupby('k').WKEND_SELNG_AMT.sum() / sel[sel.q.isin(Q[4:8])].groupby('k').THSMON_SELNG_AMT.sum(),
}).reindex(early.index).dropna()
# "Rose" (data definition): top 20% in café+bakery sales growth 2022 -> 2025/26 AND weekend share went up.
outcome['rose'] = (outcome.sales_g >= outcome.sales_g.quantile(0.8)) & (outcome.wk_shift > 0)
e = early.join(outcome, how='inner')
cand = e[~e.already_hot]                            # what we'd actually have recommended in 2022
base = e.rose.mean()
for n in (10, 20, 30):
    top = cand.head(n)
    print(f'top{n} picks (2022): {top.rose.sum()}/{n} rose = {top.rose.mean():.0%}  vs base rate {base:.0%}')
print('\nTop-20 picks as of 2022 and what happened:')
print(cand.head(20)[['score', 'sales_g', 'wk_shift', 'rose']].round(3).to_string())

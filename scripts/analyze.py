"""Score every 행정동 on four '뜬다' indicators, backtest the formula, write data/results.json."""
import json
import pandas as pd

L = lambda f: pd.DataFrame(json.load(open(f'data/{f}.json')))
flp, ix, stor, sel = L('VwsmAdstrdFlpopW'), L('VwsmAdstrdIxQq'), L('VwsmAdstrdStorW'), L('VwsmAdstrdSelngW')
GU = dict(zip('11110 11140 11170 11200 11215 11230 11260 11290 11305 11320 11350 11380 11410 11440 11470 11500 11530 11545 11560 11590 11620 11650 11680 11710 11740'.split(),
              '종로구 중구 용산구 성동구 광진구 동대문구 중랑구 성북구 강북구 도봉구 노원구 은평구 서대문구 마포구 양천구 강서구 구로구 금천구 영등포구 동작구 관악구 서초구 강남구 송파구 강동구'.split()))
for d in (flp, ix, stor, sel):
    d['q'] = d.STDR_YYQU_CD.astype(int)
    d['k'] = d.ADSTRD_CD.str[:5].map(GU) + ' ' + d.ADSTRD_CD_NM
flp['young'] = flp.AGRDE_20_FLPOP_CO + flp.AGRDE_30_FLPOP_CO
sel['young_amt'] = sel.AGRDE_20_SELNG_AMT + sel.AGRDE_30_SELNG_AMT

# Already-popular areas the brief rules out, plus ones that broke out during the data window.
KNOWN_HOT = {'성동구 성수1가1동', '성동구 성수1가2동', '성동구 성수2가1동', '성동구 성수2가3동', '마포구 연남동', '마포구 서교동',
             '마포구 합정동', '마포구 망원1동', '용산구 한남동', '용산구 이태원1동', '중구 을지로동', '용산구 한강로동', '중구 신당동',
             '종로구 종로1·2·3·4가동', '종로구 삼청동', '강남구 신사동', '강남구 압구정동', '강남구 청담동', '영등포구 문래동', '용산구 용산2가동'}


def window(qs):
    return lambda d: d[d.q.isin(qs)]


def score(base_q, now_q):
    b, n = window(base_q), window(now_q)
    g = lambda d, col: n(d).groupby('k')[col].sum() / b(d).groupby('k')[col].sum() - 1
    share = lambda w, col: w(sel).groupby('k')[col].sum() / w(sel).groupby('k').THSMON_SELNG_AMT.sum()
    df = pd.DataFrame({
        'weekend_shift': share(n, 'WKEND_SELNG_AMT') - share(b, 'WKEND_SELNG_AMT'),
        'young_spend_shift': share(n, 'young_amt') - share(b, 'young_amt'),
        'weekend_share': share(n, 'WKEND_SELNG_AMT'),
        'young_spend_share': share(n, 'young_amt'),
        'young_growth': g(flp, 'young'),
        'store_growth': g(stor, 'SIMILR_INDUTY_STOR_CO'),
        'sales_growth': g(sel, 'THSMON_SELNG_AMT'),
        'young_level': n(flp).groupby('k').young.sum() / len(now_q),
        'stores_now': n(stor).groupby('k').SIMILR_INDUTY_STOR_CO.sum() / len(now_q),
        'stores_base': b(stor).groupby('k').SIMILR_INDUTY_STOR_CO.sum() / len(base_q),
        'sales_now': n(sel).groupby('k').THSMON_SELNG_AMT.sum() / len(now_q),
        'sales_base': b(sel).groupby('k').THSMON_SELNG_AMT.sum() / len(base_q),
    })
    last = ix[ix.q == max(now_q)].set_index('k')
    df['change_ix'] = last.TRDAR_CHNGE_IX_NM
    df['expanding'] = last.TRDAR_CHNGE_IX.isin(['LL', 'LH']).astype(float)
    df = df.dropna(subset=['young_growth', 'store_growth', 'sales_growth'])
    # Size floor: tiny bases make growth rates meaningless.
    df = df[(df.stores_base >= 15) & (df.sales_base >= df.sales_base.quantile(0.25))]
    pr = df[['young_growth', 'store_growth', 'sales_growth', 'weekend_shift', 'young_spend_shift']].rank(pct=True)
    df['score'] = 100 * (0.85 * pr.mean(axis=1) + 0.15 * df['expanding'])
    # 'Not yet popular': outside the top 10% on young foot traffic or café/bakery sales, and not a known hotspot.
    df['already_hot'] = (df.young_level >= df.young_level.quantile(0.9)) | (df.sales_now >= df.sales_now.quantile(0.9)) | df.index.isin(KNOWN_HOT)
    return df.sort_values('score', ascending=False)


Q = sorted(flp.q.unique())
now, base = Q[-4:], Q[-12:-8]                     # 2025Q3–2026Q2 vs 2023Q3–2024Q2
cur = score(base, now)

# Backtest: score as of 2022 (2022 vs 2021), then measure what happened to café/bakery sales by 2025Q3–2026Q2.
early = score(Q[:4], Q[4:8])
early['later_sales_growth'] = (sel[sel.q.isin(now)].groupby('k').THSMON_SELNG_AMT.sum() / 4) / early.sales_now - 1
early = early.dropna(subset=['later_sales_growth'])
top = early.head(int(len(early) * 0.1))
bt = {
    'n': len(early),
    'spearman': round(early.score.corr(early.later_sales_growth, method='spearman'), 3),
    'top10_median_later': round(top.later_sales_growth.median(), 3),
    'all_median_later': round(early.later_sales_growth.median(), 3),
    'cases': {k: {'rank': int(list(early.index).index(k)) + 1, 'score': round(early.score[k], 1),
                  'later_sales_growth': round(early.later_sales_growth[k], 3)}
              for k in ['중구 신당동', '용산구 한강로동', '성동구 성수2가3동', '성동구 성수1가2동', '영등포구 문래동', '마포구 망원1동'] if k in early.index},
}

picks = cur[~cur.already_hot].head(15)
out = {
    'window': {'now': [int(q) for q in now], 'base': [int(q) for q in base]},
    'n_scored': len(cur),
    'picks': [dict(name=k, **{c: (None if pd.isna(v) else (round(v, 4) if isinstance(v, float) else v)) for c, v in r.items()}) for k, r in picks.iterrows()],
    'hot_top': [dict(name=k, score=round(r.score, 1)) for k, r in cur[cur.already_hot].head(8).iterrows()],
    'backtest': bt,
}
json.dump(out, open('data/results.json', 'w'), ensure_ascii=False, indent=1, default=float)
pd.set_option('display.width', 220)
print(picks[['young_growth', 'store_growth', 'sales_growth', 'weekend_shift', 'young_spend_shift', 'weekend_share', 'young_spend_share', 'change_ix', 'stores_now', 'score']].round(3).to_string())
print(json.dumps(bt, ensure_ascii=False, indent=1))

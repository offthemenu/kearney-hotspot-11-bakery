"""Quarterly 행정동 panel of café+bakery leading indicators and 2-year forward outcomes (rolling origins)."""
import json
import numpy as np
import pandas as pd

GU = dict(zip('11110 11140 11170 11200 11215 11230 11260 11290 11305 11320 11350 11380 11410 11440 11470 11500 11530 11545 11560 11590 11620 11650 11680 11710 11740'.split(),
              '종로구 중구 용산구 성동구 광진구 동대문구 중랑구 성북구 강북구 도봉구 노원구 은평구 서대문구 마포구 양천구 강서구 구로구 금천구 영등포구 동작구 관악구 서초구 강남구 송파구 강동구'.split()))
KNOWN_HOT = {'성동구 성수1가1동', '성동구 성수1가2동', '성동구 성수2가1동', '성동구 성수2가3동', '마포구 연남동', '마포구 서교동',
             '마포구 합정동', '마포구 망원1동', '용산구 한남동', '용산구 이태원1동', '중구 을지로동', '용산구 한강로동', '중구 신당동',
             '종로구 종로1·2·3·4가동', '종로구 삼청동', '강남구 신사동', '강남구 압구정동', '강남구 청담동', '영등포구 문래동', '용산구 용산2가동'}


def load(f):
    d = pd.DataFrame(json.load(open(f'data/{f}.json')))
    d['q'] = d.STDR_YYQU_CD.astype(int)
    d['k'] = d.ADSTRD_CD.str[:5].map(GU) + ' ' + d.ADSTRD_CD_NM
    return d


sel, stor, flp, ix = load('VwsmAdstrdSelngW'), load('VwsmAdstrdStorW'), load('VwsmAdstrdFlpopW'), load('VwsmAdstrdIxQq')
s = sel.assign(young=sel.AGRDE_20_SELNG_AMT + sel.AGRDE_30_SELNG_AMT, eve=sel.TMZON_17_21_SELNG_AMT + sel.TMZON_21_24_SELNG_AMT)
s = s.groupby(['k', 'q'])[['THSMON_SELNG_AMT', 'WKEND_SELNG_AMT', 'young', 'eve', 'FML_SELNG_AMT', 'THSMON_SELNG_CO']].sum()
s.columns = ['sales', 'wk', 'young', 'eve', 'fml', 'tx']
t = stor.groupby(['k', 'q'])[['SIMILR_INDUTY_STOR_CO', 'FRC_STOR_CO', 'OPBIZ_STOR_CO', 'CLSBIZ_STOR_CO']].sum()
t.columns = ['stores', 'frc', 'opn', 'cls']
f = flp.assign(yf=flp.AGRDE_20_FLPOP_CO + flp.AGRDE_30_FLPOP_CO).groupby(['k', 'q'])[['yf', 'TOT_FLPOP_CO']].sum()
f.columns = ['yflp', 'flp']
x = ix.groupby(['k', 'q']).TRDAR_CHNGE_IX.first().rename('ix')
P = pd.concat([s, t, f, x], axis=1).sort_index()
Q = sorted(P.index.get_level_values('q').unique())

# Rolling 4-quarter sums (stock variables averaged).
g = P.groupby(level='k')
R = pd.DataFrame({c: g[c].transform(lambda v: v.rolling(4).sum()) for c in ['sales', 'wk', 'young', 'eve', 'fml', 'tx', 'opn', 'cls', 'yflp', 'flp']})
for c in ['stores', 'frc']:
    R[c] = g[c].transform(lambda v: v.rolling(4).mean())
R['ix'] = P.ix


def at(i):
    return R.xs(Q[i], level='q')


def features(i):
    """Signals knowable at end of quarter Q[i] (uses Q[i-7]..Q[i])."""
    a, b = at(i), at(i - 4)
    F = pd.DataFrame(index=a.index)
    F['sales_yoy'] = a.sales / b.sales - 1                       # baseline: momentum
    F['log_size'] = np.log(a.sales)                              # baseline: size / mean reversion
    F['stores_yoy'] = a.stores / b.stores - 1
    F['young_flp_yoy'] = a.yflp / b.yflp - 1
    F['wk_shift'] = a.wk / a.sales - b.wk / b.sales
    F['young_spend_shift'] = a.young / a.sales - b.young / b.sales
    F['young_spend_lvl'] = a.young / a.sales
    F['eve_shift'] = a.eve / a.sales - b.eve / b.sales
    F['fml_lvl'] = a.fml / a.sales
    F['indie_lvl'] = 1 - a.frc / a.stores                        # independent-shop share
    F['indie_shift'] = (1 - a.frc / a.stores) - (1 - b.frc / b.stores)
    F['open_rate'] = a.opn / a.stores                            # entrepreneurs entering
    F['net_open'] = (a.opn - a.cls) / a.stores
    F['sps_yoy'] = (a.sales / a.stores) / (b.sales / b.stores) - 1  # demand outpacing supply
    F['ticket_yoy'] = (a.sales / a.tx) / (b.sales / b.tx) - 1    # spend per visit
    F['ix_dyn'] = a.ix.isin(['LL', 'LH']).astype(float)
    # Universe: big enough to measure, not already popular at the time.
    ok = (a.stores >= 15) & (a.sales >= a.sales.quantile(0.25))
    hot = (a.yflp >= a.yflp.quantile(0.9)) | (a.sales >= a.sales.quantile(0.9)) | a.index.isin(KNOWN_HOT)
    F['eligible'] = ok & ~hot
    return F.replace([np.inf, -np.inf], np.nan)


def outcome(i, h=8):
    a, z = at(i), at(i + h)
    y = pd.DataFrame(index=a.index)
    y['fwd_growth'] = z.sales / a.sales - 1
    y['fwd_wk_shift'] = z.wk / z.sales - a.wk / a.sales
    return y

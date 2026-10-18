"""Rolling-origin backtest of each candidate metric. Train origins pick metrics; test origins are only reported."""
import sys; sys.path.insert(0, 'scripts')
import pandas as pd
from panel import Q, features, outcome

TRAIN = [Q.index(q) for q in (20224, 20231, 20232, 20233)]
TEST = [Q.index(q) for q in (20234, 20241, 20242)]
FEATS = ['sales_yoy', 'log_size', 'stores_yoy', 'young_flp_yoy', 'wk_shift', 'young_spend_shift', 'young_spend_lvl',
         'eve_shift', 'fml_lvl', 'indie_lvl', 'indie_shift', 'open_rate', 'net_open', 'sps_yoy', 'ticket_yoy', 'ix_dyn']
TOPN = 20


def frame(i):
    d = features(i).join(outcome(i))
    d = d[d.eligible].dropna(subset=['fwd_growth', 'fwd_wk_shift'])
    d['rose'] = (d.fwd_growth >= d.fwd_growth.quantile(0.8)) & (d.fwd_wk_shift > 0)
    return d


def stats(origins, sign=None):
    rows = {}
    for f in FEATS:
        ic, hit, base = [], [], []
        for i in origins:
            d = frame(i).dropna(subset=[f])
            ic.append(d[f].corr(d.fwd_growth, method='spearman'))
            s = 1 if sign is None else sign[f]
            top = d.sort_values(f, ascending=s < 0).head(TOPN) if f != 'ix_dyn' else d[d[f] == (1 if s > 0 else 0)]
            hit.append(top.rose.mean()); base.append(d.rose.mean())
        rows[f] = dict(ic=pd.Series(ic).mean(), ic_same_sign=int((pd.Series(ic) > 0).sum()) if pd.Series(ic).mean() > 0 else int((pd.Series(ic) < 0).sum()),
                       hit=pd.Series(hit).mean(), base=pd.Series(base).mean())
    return pd.DataFrame(rows).T


if __name__ == '__main__':
    tr = stats(TRAIN)
    sign = {f: (1 if tr.loc[f, 'ic'] >= 0 else -1) for f in FEATS}
    tr = stats(TRAIN, sign)
    te = stats(TEST, sign)
    out = pd.concat({'train': tr, 'test': te}, axis=1).round(3)
    out.insert(0, 'dir', pd.Series(sign))
    pd.set_option('display.width', 200)
    print(out.sort_values(('train', 'ic'), key=abs, ascending=False).to_string())

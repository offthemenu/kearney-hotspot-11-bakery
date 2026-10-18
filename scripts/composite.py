"""Select metrics by a fixed rule on TRAIN origins, combine, and report on held-out TEST origins."""
import sys; sys.path.insert(0, 'scripts')
import pandas as pd
from evaluate import TRAIN, TEST, FEATS, TOPN, frame, stats

tr0 = stats(TRAIN)
sign = {f: (1 if tr0.loc[f, 'ic'] >= 0 else -1) for f in FEATS}
tr = stats(TRAIN, sign)
# Rule fixed before looking at TEST: consistent sign on all 4 train origins, top-20 hit >= 1.5x base.
CHOSEN = [f for f in FEATS if f != 'ix_dyn' and tr.loc[f, 'ic_same_sign'] == len(TRAIN) and tr.loc[f, 'hit'] >= 1.5 * tr.loc[f, 'base']]


def comp(d):
    return sum(sign[f] * d[f].rank(pct=True) for f in CHOSEN) / len(CHOSEN)


def run(origins, label):
    rows = []
    for i in origins:
        d = frame(i).dropna(subset=CHOSEN)
        d['score'] = comp(d)
        top = d.nlargest(TOPN, 'score')
        mom = d.nlargest(TOPN, 'sales_yoy')
        rows.append(dict(origin=i, n=len(d), base=d.rose.mean(), composite=top.rose.mean(), momentum_only=mom.rose.mean(),
                         ic=d.score.corr(d.fwd_growth, method='spearman'), top_med_growth=top.fwd_growth.median(), all_med_growth=d.fwd_growth.median()))
    r = pd.DataFrame(rows)
    print(f'\n[{label}]'); print(r.round(3).to_string(index=False))
    print('mean:', r.drop(columns=['origin', 'n']).mean().round(3).to_dict())


if __name__ == '__main__':
    print('chosen:', {f: sign[f] for f in CHOSEN})
    run(TRAIN, 'train'); run(TEST, 'held-out test')

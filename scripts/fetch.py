"""Pull Seoul 상권분석서비스 (행정동) data into data/*.json. Reads SEOUL_OPEN_API_KEY from .env."""
import json, urllib.request, concurrent.futures as cf, pathlib

KEY = next(l.split('=', 1)[1].strip() for l in open('.env') if l.startswith('SEOUL_OPEN_API_KEY='))
OUT = pathlib.Path('data')
FNB = {'CS100005', 'CS100010'}  # 제과점, 커피-음료


def page(svc, a, b, q=''):
    url = f'http://openapi.seoul.go.kr:8088/{KEY}/json/{svc}/{a}/{b}/{q}'
    for _ in range(3):
        try:
            r = json.load(urllib.request.urlopen(url, timeout=60)).get(svc) or {}
            return r.get('list_total_count') or 0, r.get('row') or []
        except Exception:
            pass
    raise RuntimeError(f'{svc} {a}-{b} {q} failed')


def pull(svc, q='', keep=lambda r: True):
    total, first = page(svc, 1, 1000, q)
    rows = first
    with cf.ThreadPoolExecutor(12) as ex:
        for _, rs in ex.map(lambda a: page(svc, a, a + 999, q), range(1001, total + 1, 1000)):
            rows += rs
    return [r for r in rows if keep(r)]


quarters = [f'{y}{q}' for y in range(2021, 2027) for q in range(1, 5) if f'{y}{q}' <= '20262']
for svc in ['VwsmAdstrdFlpopW', 'VwsmAdstrdRepopW', 'VwsmAdstrdIxQq']:
    rows = pull(svc)
    (OUT / f'{svc}.json').write_text(json.dumps(rows, ensure_ascii=False))
    print(svc, len(rows), min(r['STDR_YYQU_CD'] for r in rows), max(r['STDR_YYQU_CD'] for r in rows))

for svc in ['VwsmAdstrdStorW', 'VwsmAdstrdSelngW']:
    rows = []
    for q in quarters:
        if page(svc, 1, 1, q)[0]:
            rows += pull(svc, q, lambda r: r['SVC_INDUTY_CD'] in FNB)
    (OUT / f'{svc}.json').write_text(json.dumps(rows, ensure_ascii=False))
    print(svc, len(rows), min(r['STDR_YYQU_CD'] for r in rows), max(r['STDR_YYQU_CD'] for r in rows))

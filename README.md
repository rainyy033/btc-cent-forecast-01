# btc-cent-forecast

Entry for [make.fun btc-cent-forecast-01](https://make.fun/bounty/btc-cent-forecast-01).

Forecasts Bitcoin's USDC price 240 minutes ahead from 4,320 one-minute closes.

## Model

Shrunk 12h momentum over persistence, constants fixed a priori (no future-data fitting):

```
guess = last_close + 0.6 * ((last - close_720min_ago) / 720) * 240
```

Deterministic, stdlib-only Python 3.13, ~0.02s per case.

## Scoring

The score is the mean absolute error in cents: `100 × |guess − actual|`, averaged
over the cases (lower is better). The house persistence baseline — which guesses
each checkpoint's own close — measures **44521.576667 cents** (mean error
**$445.215767**) on the sealed practice set. A prize needs to beat that on the
final, with every case valid.

## Output

One `/output/<id>.out` per `/input/<id>.in`, exactly
`{"forecasts":[{"case":"<id>","price":<number>}]}`, the price clamped to
`[0.00001, 9999999.99999]` and rounded to 5 decimals. A case with no prices (or
a non-finite last price) is raised as invalid, which the scorer treats as
guessing the checkpoint's own close.

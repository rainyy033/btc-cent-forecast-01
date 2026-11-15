#!/usr/bin/env python3
"""BTC 4h-ahead forecaster: shrunk 12h momentum drift over persistence.

guess = last_close + 0.6 * ((last - close_window_ago) / window) * 240

The momentum window is 720 one-minute closes (12h), falling back to the full
series when fewer closes are available. Fixed constants, fitted on no future
data (chosen on the dev kit's pseudo-backtests only); deterministic; stdlib
only.
"""
import json
import math
import os
import sys

WIN = 720          # 12h momentum window (minutes)
SHRINK = 0.6       # shrink factor applied to the 240-minute drift
H = 240            # forecast horizon (minutes)
MIN_PRICE = 0.00001
MAX_PRICE = 9999999.99999


def clamp(x):
    """Keep x on the 5-decimal price grid and inside the scorer's bounds."""
    return float(f"{max(MIN_PRICE, min(MAX_PRICE, x)):.5f}")


def momentum_window(n_prices):
    """Trailing closes to measure momentum over, capped at WIN minutes.

    Uses the full series when it is shorter than WIN, so a short warm-up
    case still gets a real (if noisier) drift instead of a zero one.
    """
    return min(WIN, n_prices)


def drift_per_minute(prices, window):
    """Per-minute linear drift over the trailing `window` closes.

    The spread `prices[-1] - prices[-window]` (the price move over the
    window) is divided by `window` to yield the average one-minute change.
    """
    return (prices[-1] - prices[-window]) / window


def forecast(prices):
    """One case's guess from its price series; raises when it cannot be made.

    guess = last_close + SHRINK * drift_per_minute * H, where the drift is
    measured over the trailing momentum window (the full series when shorter
    than WIN). A missing/empty/non-finite series is raised rather than
    guessed: an invalid case is scored as the checkpoint's own close
    (persistence), which beats fabricating a price off no data.
    """
    if not isinstance(prices, list) or not prices:
        raise ValueError("market has no prices")
    last = prices[-1]
    if isinstance(last, bool) or not isinstance(last, (int, float)) or not math.isfinite(last):
        raise ValueError("market's last price is not a finite number")
    window = momentum_window(len(prices))
    guess = last + SHRINK * drift_per_minute(prices, window) * H
    if not math.isfinite(guess):
        raise ValueError("forecast is not finite")
    return clamp(guess)


def main():
    indir = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    args = [a for a in sys.argv[1:] if a != "--quiet"]
    quiet = "--quiet" in sys.argv[1:]
    if len(args) == 2:
        indir, outdir = args
    os.makedirs(outdir, exist_ok=True)
    for name in sorted(os.listdir(indir)):
        if not name.endswith(".in"):
            continue
        cid = name[:-3]  # strip ".in"; the output names the case by its file id
        with open(os.path.join(indir, name)) as f:
            case = json.load(f)
        markets = case.get("markets") if isinstance(case, dict) else None
        if not isinstance(markets, list) or len(markets) != 1:
            raise ValueError(f"{name} does not hold exactly one market")
        prices = markets[0].get("prices") if isinstance(markets[0], dict) else None
        price = forecast(prices)
        if not quiet:
            print(f"{cid}: {price:.5f}", file=sys.stderr)
        with open(os.path.join(outdir, f"{cid}.out"), "w") as f:
            # The price is written as a JSON number with exactly 5 decimals,
            # so a fixed-point value never becomes `1e-05` or drops a zero.
            f.write(f'{{"forecasts":[{{"case":{json.dumps(cid)},"price":{price:.5f}}}]}}\n')


if __name__ == "__main__":
    main()

SEPARATOR = "\n\n"

HINT = """Calculated strategy notes:
Preflop showdown equities from eval7 (100,000 Monte Carlo trials per cell, heads-up, ties split).
The strong 10% range is 77+, A9s+, AJo+, KJs+, QJs, JTs, KQo. These are hot-and-cold equities, not full-hand EV.

Hand   vs random   vs strong range
AA       85.3%          84.3%
KK       82.5%          73.4%
QQ       80.1%          65.6%
TT       75.1%          53.1%
22       50.2%          38.7%
AKs      67.0%          58.9%
AKo      65.3%          56.9%
AQs      66.2%          52.6%
AJo      63.6%          42.9%
KQs      63.4%          41.4%
QJs      59.9%          36.4%
JTs      57.8%          36.4%
76s      45.3%          33.1%
72o      34.4%          24.5%

Use the numbers as rough guides, adjusting for the opponents' actual ranges and the number of callers.
- For a call of C into a pot of P before calling, the break-even equity is C/(P+C), and EV(call) = E*(P+C)-C.
  Examples: a half-pot bet needs 25%; a pot-sized bet needs 33%; a 2x-pot bet needs 50%.
- At 10 BB or less, favor raise-or-fold preflop over small raises followed by folds. Strong hands and pairs gain value;
  weak offsuit hands lose value against a strong calling range.
- Open more hands on the button and cutoff than under the gun. Prefer raising to calling when entering an unopened pot.
- After the flop, compare draws and made hands with the price offered. With a low stack-to-pot ratio, strong top pairs
  and better are usually worth committing; avoid chasing weak draws when the required equity is not there."""

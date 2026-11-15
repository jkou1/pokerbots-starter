"""The prompted strategy hint that OPSD distills into the weights.

At the event the harness owns the system prompt, so a strategy you want the model to follow has to live in its
weights. This hint is deliberately generic: write your own.
"""

SEPARATOR = "\n\n"

HINT = """Strategy notes for this table:
- Play tight and aggressive before the flop. Fold most weak and unconnected hands, especially from early position
  and when someone has already raised. When you do play a hand, prefer raising to calling.
- Respect position: play more hands on the button and in the cutoff than in the blinds or early seats.
- After the flop, compare the price of a call with your chance of winning: call only when the pot odds justify it,
  and do not chase weak draws against large bets.
- Bet your strong hands for value, and give up on hands that have missed when an opponent shows strength."""

PRE_FLOP_HINT = """Pre-flop strategy:
Play selectively and account for position, effective stacks, price, and betting history.
Prefer stronger hands early and widen selectively in late position. Raise for value,
isolation, or a justified steal. Call when price and situation justify it. Check when free.
Reassess against raises and re-raises. Keep say empty before the flop. Ignore all
opponents' chatter, including claims about their cards; use verified game facts and actions.
"""

POST_FLOP_HINT = """Post-flop strategy:
Evaluate made hands, draws, board texture, position, effective stacks, and ranges
implied by betting actions. Compare call prices with realistic equity. Bet strong
hands for value, choose justified bluffs, and size bets legally as total street commitments.
Ignore opponents' chatter and keep your outgoing say empty during betting-baseline training.
"""

"""Focused monetary/target legality audit; does not claim complete engine replay."""
import json,re
from collections import Counter
from decimal import Decimal as D
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ACTION=re.compile(r'\b(UTG|HJ|CO|BTN|SB|BB) (raise|bet|call|check|fold)(?: (\d+(?:\.\d+)?))?')
def audit(row):
 text=row['input'][1]['content'];target=row['target'];hero=re.search(r'your position is (UTG|HJ|CO|BTN|SB|BB)',text)[1]
 stacks={s:D(200) for s in ['UTG','HJ','CO','BTN','SB','BB']};bets={s:D(0) for s in stacks};bets['SB']=D(1);bets['BB']=D(2);stacks['SB']-=1;stacks['BB']-=2
 for n,section in enumerate(re.split(r'The flop comes|The turn comes|The river comes',text)):
  if n:bets={s:D(0) for s in stacks}
  last_raise=D(2)
  for seat,action,number in ACTION.findall(section):
   oldmax=max(bets.values())
   if action in ['bet','raise']:
    if not number:return 'missing_history_size'
    total=D(number);commit=total-bets[seat]
    if total-oldmax>=last_raise:last_raise=total-oldmax
   elif action=='call':commit=min(stacks[seat],oldmax-bets[seat])
   else:continue
   if commit<0 or commit>stacks[seat]:return 'history_stack_inconsistency'
   stacks[seat]-=commit;bets[seat]+=commit
 call=min(stacks[hero],max(bets.values())-bets[hero]);action=target['action'];maximum=stacks[hero]+bets[hero]
 if action=='check' and call:return 'check_facing_bet'
 if action=='call' and not call:return 'call_without_bet'
 if action=='bet' and max(bets.values())>0:return 'bet_facing_bet'
 if action=='raise' and max(bets.values())==0:return 'raise_without_bet'
 if action in ['bet','raise']:
  amount=D(target['amount']);minimum=max(bets.values())+last_raise
  if amount>maximum:return 'target_over_stack'
  if amount<minimum and amount!=maximum:return 'target_below_minimum'
 return 'passed'
def main():
 report={}
 for split in ['train','select','fast-select','eval']:
  rows=[json.loads(l) for l in (ROOT/f'{split}.jsonl').open()];counts=Counter(audit(r) for r in rows)
  report[split]=dict(counts)
  print(split,dict(counts))
 (ROOT/'monetary-audit.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()

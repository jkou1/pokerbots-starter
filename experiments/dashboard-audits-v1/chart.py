import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
fig,axes=plt.subplots(1,2,figsize=(11,4.7),layout='constrained')
for name,label,color in [('continuation','Incumbent continuation','#2563eb'),('base','Independent base','#d97706')]:
 r=json.loads((ROOT/f'{name}-action-ce.json').read_text());windows=[r['windows'][f'{s}-{s+9}'] for s in [0,10,20,30]]
 for ax,values in [(axes[0],[x['class_balanced_action_ce'] for x in windows]),(axes[1],[x['per_action']['bet']['action_ce'] for x in windows])]:
  ax.plot(range(4),values,marker='o',linewidth=2.3,color=color,label=label)
  ax.set_xticks(range(4),['0–9','10–19','20–29','30–39']);ax.grid(axis='y',alpha=.2);ax.spines[['top','right']].set_visible(False);ax.set_xlabel('Optimizer update window');ax.set_ylabel('Cross-entropy (nats; lower is better)')
  for x,y in [(0,values[0]),(3,values[3])]:ax.annotate(f'{y:.2f}',(x,y),xytext=(0,8 if name=='continuation' else -16),textcoords='offset points',ha='center',fontsize=9,color=color)
axes[0].set_ylim(.35,1.4)
axes[1].set_ylim(.5,2.3)
axes[0].set_title('Action arguments, balanced across classes',fontsize=11)
axes[1].set_title('Bet argument only',fontsize=11)
axes[0].legend(frameon=False,loc='upper right',fontsize=9)
fig.suptitle('SFT action learning, excluding protocol and tool syntax',fontsize=15,fontweight='bold')
fig.supxlabel('640 training examples per window. Different minibatches; these curves do not measure poker performance.',fontsize=9)
fig.savefig(ROOT/'ACTION_TOKEN_CE.png',dpi=170)
fig.savefig(ROOT/'ACTION_TOKEN_CE.svg')
print('Saved PNG and SVG action-CE chart.')

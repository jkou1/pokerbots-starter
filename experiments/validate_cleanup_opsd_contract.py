"""CPU-only structural audit; no model, upload, environment or training calls."""
import json
from ac2.runtime import HintedTask,HintSelection,HintMutation,Message,FunctionCall,FunctionCallOutput
from ac2.runtime.base.task_types import satisfied_types
from ac2.runtime.base.hinter import validate_hint_selection

def build(prompt,reply,tools,hint,provenance):
    assert prompt and isinstance(prompt[0],Message) and prompt[0].role=='system'
    assert reply and hint.strip()
    task=HintedTask(input=prompt+reply,env_params={'tools':tools},tags={'provenance':provenance},opsd_hint_selections=[HintSelection(hint=hint,rollout_prefix_len=len(prompt),mutation=HintMutation(item_boundary=1,action='append_to_previous_item',separator='\n\n'))])
    assert [x.model_dump()for x in task.input[:len(prompt)]]==[x.model_dump()for x in prompt]
    assert [x.model_dump()for x in task.input[len(prompt):]]==[x.model_dump()for x in reply]
    validate_hint_selection(task.input,task.opsd_hint_selections[0]);assert 'hinted'in satisfied_types(task)
    return task

if __name__=='__main__':
    # Synthetic structural fixtures, never training records or claimed model evidence.
    prompt=[Message(role='system',content='original'),Message(role='user',content='past'),FunctionCall(call_id='old',name='submit_action',arguments='{"action":"check"}'),FunctionCallOutput(call_id='old',output='accepted'),Message(role='user',content='cleanup original memory')]
    tools=[{'type':'function','name':'update_scratchpad','description':'memory','parameters':{'type':'object','properties':{'contents':{'type':'string'}},'required':['contents']}}]
    results={}
    for label,reply in {'valid':[FunctionCall(call_id='new',name='update_scratchpad',arguments=json.dumps({'contents':'short'}))],'overlong':[FunctionCall(call_id='new',name='update_scratchpad',arguments=json.dumps({'contents':'x'*5001}))],'malformed_arguments':[FunctionCall(call_id='new',name='update_scratchpad',arguments='{bad')],'wrong_tool':[FunctionCall(call_id='new',name='submit_action',arguments='{"action":"fold"}')],'missing_call':[Message(role='assistant',content='plain response')]}.items():
        task=build(prompt,reply,tools,'Teacher-only compression hint',{'synthetic_validation_only':True});results[label]={'locally_accepted':True,'prefix_items':task.opsd_hint_selections[0].rollout_prefix_len,'historical_items_preserved':True}
    print(json.dumps({'scope':'Synthetic local structural validation only; not server renderer/permission/loss proof','cases':results},indent=2))

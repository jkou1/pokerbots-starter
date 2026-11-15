"""Audit managed Qwen targets against their actual prompt boundary.

Current managed SFT places the one newline in student_prompt. Older samples
placed it at the start of sampled_tokens. Require the combined boundary rather
than adding another newline or rejecting valid current samples.
"""
def audit_target(payload):
 tokens=payload['sampled_tokens'];mask=payload['loss_mask'];text=''.join(tokens)
 prompt=payload['student_prompt']
 if not tokens:raise ValueError('Empty supervised target')
 if prompt.endswith('<think>\n'):
  expected='Tool call follows.'
  location='prompt'
 elif prompt.endswith('<think>'):
  expected='\nTool call follows.'
  location='target'
 else:raise ValueError('Training prompt does not end at the expected reasoning prefill')
 if not text.startswith(expected):raise ValueError('Combined prompt/target boundary mismatches single-newline official prefill')
 if '</think>' not in tokens or mask[tokens.index('</think>')]!=1:raise ValueError('Reasoning close is not explicitly supervised')
 if '<tool_call>' not in text or text.index('</think>')>text.index('<tool_call>'):raise ValueError('Tool call precedes reasoning close')
 return {'response_tokens':len(tokens),'first_target_token':tokens[0],'prefill_newline_location':location,'reasoning_close_supervised':True,'combined_boundary_verified':True}

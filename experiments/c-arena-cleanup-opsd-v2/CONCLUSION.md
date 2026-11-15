# V2 stopped: closed-world hints did not meet the frozen gate

All ten fresh TRAIN pairs completed, with twenty authentic OWN10 responses and no retries. All responses finished with `tool_calls`; full request and response bodies were captured upfront without authentication headers. The saved reasoning, text and tool calls exactly match each captured response.

Four hinted notes exceeded the unchanged1500-character acceptance cap: cases2/5/8/10 produced5703/1629/3343/5231characters. Therefore strict useful acceptance is at most6/10, below the required8/10 regardless of remaining factual review. The conservative all-claims parser accepted zero replies in either arm: outputs continued to add forbidden narrative, drop provided prior facts, or include unverifiable historical claims. This parser count is not presented as an exhaustive semantic judgment of alternate factual formatting; the length failures alone establish the stop decision.

No further hint variants, remaining probes, training or promotion are authorized. V1 remains closed negative. The two pilots used forty calls total. These results show that the particular teacher hints did not reliably constrain this OWN10 policy; native offline OPSD training itself was not attempted or evaluated.

CPU template rendering preserved authentic new reasoning and original history, with one thinking close before real tool calls. The actual unhinted reply plus prefix reached8243student tokens and8551hinted teacher tokens, exceeding8192; future work would require measured caps above those values. No managed training mask was claimed or tested.

See `paired-first10-score.json`, `paired-first10-finish-audit.json` and `actual-reply-render-audit.json`. Exact private source messages, replies and HTTP bodies remain ignored local evidence.

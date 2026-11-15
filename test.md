test -n "$AC2_API_KEY" && echo "API key is set" || echo "API key is missing"

curl --http1.1 -sS -D /tmp/ac2-headers.txt \
  -o /tmp/ac2-body.txt \
  -X POST https://inference.appliedcompute.com/v1/chat/completions \
  -H "Authorization: Bearer $AC2_API_KEY" \
  -H "Content-Type: application/json" \
  --data '{
    "model": "vals-hackathon/step2",
    "messages": [
      {"role": "user", "content": "Call submit_action."}
    ],
    "tools": [{
      "type": "function",
      "function": {
        "name": "submit_action",
        "description": "Submit your action.",
        "parameters": {
          "type": "object",
          "properties": {
            "action": {
              "type": "string",
              "enum": ["fold", "check", "call", "bet", "raise"]
            }
          },
          "required": ["action"]
        }
      }
    }],
    "max_completion_tokens": 500
  }'

head -n 20 /tmp/ac2-headers.txt
python3 -m json.tool /tmp/ac2-body.txt
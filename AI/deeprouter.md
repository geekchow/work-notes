# How to user deeprouter api 

make api call

```shell
curl https://deeprouter.top/v1/chat/completions \
   -H 'Content-Type: application/json' \
   -H 'Authorization: Bearer token ' \
   -d '{
   "model": "gpt-5.2-chat",
   "messages": [{"role": "user", "content": "Say this is a test!"}],
   "temperature": 0.7
 }'
```

Response

```json
{
  "id": "chatcmpl-D9pjMtsOxsQcuhWuerWcsl8VT1Izj",
  "object": "chat.completion",
  "created": 1771236176,
  "model": "gpt-5.2-chat-2025-12-11",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "This is a test!",
        "refusal": null,
        "annotations": []
      },
      "logprobs": null,
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 9,
    "total_tokens": 21,
    "prompt_tokens_details": {
      "cached_tokens": 0,
      "audio_tokens": 0
    },
    "completion_tokens_details": {
      "reasoning_tokens": 0,
      "audio_tokens": 0,
      "accepted_prediction_tokens": 0,
      "rejected_prediction_tokens": 0
    }
  },
  "system_fingerprint": null
}

```
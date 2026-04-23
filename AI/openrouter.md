```shell
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -H "HTTP-Referer: https://localhost" \
  -H "X-Title: curl-test" \
  -d '{
    "model": "minimax/minimax-m2.5:free",
    "messages": [{"role": "user", "content": "Say hello"}]
  }' | jq
```

available model for me: `gpt-oss-120b`, `gpt-oss-120b:free`

```shell

curl https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -H "HTTP-Referer: https://localhost" \
  -H "X-Title: curl-test" \
  -d '{
    "model": "openai/gpt-4.1-nano",
    "messages": [{"role": "user", "content": "Say hello"}]
  }' | jq


  ```
gpt model will get error 

  ```json
{
  "error": {
    "message": "The request is prohibited due to a violation of provider Terms Of Service.",
    "code": 403,
    "metadata": {
      "provider_name": null
    }
  },
  "user_id": "user_3CgzUYhpKWnHfeBlhydn1e6x0E4"
}
  ```

all model info could be found [fulllist of models in openrouter](./openrouter.json)
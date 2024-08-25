## LLM Google Search Agent

This agent incorporates the power of Google Search Engine into your LLM, enhancing its capibilities and providing richer responses.

pip install -r requirements.txt


##### Notes for prompting models
https://stackoverflow.com/questions/76192496/openai-v1-completions-vs-v1-chat-completions-end-points
Types of endpoints:
1. /v1/completions endpoint is for the old models such as DaVinci. It is a very powerful model that gets instruction and produces output.

2. The /v1/chat/completions API is for the newer - chat models (as Oleg mentioned). gpt-3.5-turbo is great because it can do everything DaVinci can but its cheaper(1/10 the cost) the down side is that - for it to perform the same as DaVinci it might require bigger input and the input might be more complex.


**SAMPLE OF CHAT: If you want to use chat gpt models, you need to use /chat/completions API, but your request has to be adjusted.**

prompt = f"Rate the following review as an integer from 1 to 5, where 1 is the worst and 5 is the best: \"{review}\""

response = openai.ChatCompletion.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "user", "content": prompt}
  ]
)

/v1/chat/completions: gpt-4, gpt-4-0314, gpt-4-32k, gpt-4-32k-0314, gpt-3.5-turbo, gpt-3.5-turbo-0301
/v1/completions:    text-davinci-003, text-davinci-002, text-curie-001, text-babbage-001, text-ada-001

The chat model performs best when you give examples.

For DaVinci (Or other models based on /v1/completions API) the input would look like an instruction: "Creates two to three sentence short horror stories from the topic 'wind'."

For the chat models the input would look as a chat:

```
Two-Sentence Horror Story: He always stops crying when I pour the milk on his cereal. I just have to remember not to let him see his face on the carton.
    
Topic: Wind
Two-Sentence Horror Story:
The output would be completion of the chat. For example: The wind howled through the night, shaking the windows of the house with a sinister force. As I stepped outside, I could feel it calling out to me, beckoning me to follow its chilling path. 
```


import openai


openai.api_key = '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'

response = openai.Completion.create(
  model="text-davinci-003",
  prompt="Tell me the history of Europe in summary",
  temperature=0,
  max_tokens=100,
  top_p=1,
  frequency_penalty=0.0,
  presence_penalty=0.0,
  stop=["\n"]
)

print(response)
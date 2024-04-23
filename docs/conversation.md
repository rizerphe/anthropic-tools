# Conversations

For assistant-type applications, `Conversation` is the most intuitive tool. It allows you to store messages and generate new ones using AI or calling a function you provide.

A conversation contains two things:

- the messages in the conversation.
- a skill (composed from a list of [skills](skills) and a list of [`AnthropicTool`](anthropic_tools.AnthropicTool)s inherent to the conversation)

When initializing the conversation, you can pass in the list of skills and the model to use (and your Azure deployment ID if using that).

## Managing messages

The main feature of a conversation is its management of messages. You can either use `conversation.messages` (which is a list of anthropic ToolsBetaMessageParam` objects - it's a typed dictionary) to add, remove, or modify messages, or use these tools:

```python
conversation.add_message("Hi there")
conversation.add_message({
    "role": "assistant",
    "content": "Hello! How can I assist you today?"
})
conversation.add_messages([{"content": "No.", "role": "assistant"}, "Oh ok"])  # Adding several at once
conversation.pop_message(0)  # Delete the first one
conversation.clear_messages()
```

## Managing skills

A conversation also includes the skills - the tools the AI can use. You can either provide your skills when creating the conversation or add skills/tools like this:

```python
conversation.add_skill(skill)
conversation.add_function(anthropic_tool)

@conversation.add_tool
def my_awesome_function(...):
    ...

@conversation.add_tool(
    name="my_really_amazing_function",
    description="The most amazing function of them all",
    save_return=True,
    serialize=False,
    interpret_as_response=False
)
def my_amazing_function():
    return ""

conversation.remove_tool(anthropic_tool)
conversation.remove_tool(my_awesome_function)
conversation.remove_tool("my_really_amazing_function")
```

All of the keyword arguments passed to `add_tool` are optional; most of them are the same as those an [AnthropicTool](anthropic_tools.AnthropicTool) inherently has:

- `name` - the overwritten function name, otherwise will default to the function name
- `description` - the overwritten function description sent to the AI - will use the description from the docstring by default
- `save_return` - whether to send the return value of the function back to the AI; some functions - mainly those that don't return anything - don't need to do this
- `serialize` - whether to serialize the function's return value before sending the result back to the AI; Anthropic expects a tool use result to be a string; if this is False, `str()` will run on the function return. Otherwise, it will use JSON serialization, so if `serialize` is set to True, the function return needs to be JSON-serializable. If interpret_as_response is set to True and serialize is set to False, the function should return the list of blocks that will be sent to the AI. The primary use case for this is when you want to send images to Claude as part of the function response - you can also return a lost of [`ToolOutput`](anthropic_tools.ToolOutput)s - they're handled separately, so that proper tool IDs are integrated into the response where possible.
- `interpret_as_response` - whether to interpret the return value of the function (the serialized one if `serialize` is set to True) as the response from the AI

You can read more about how to use skills [here](skills).

## Generating messages

The point of a conversation is to use the AI to generate responses. The easiest way to do this is through the `ask` method:

```python
response = conversation.ask("Your input data")

# This will entirely clear the conversation, but not affect the skills:
conversation.clear_messages()
# The max_tokens argument is per message, not per conversation
conversation.ask("Your input data", max_tokens=4096)
```

The tool will then repeatedly get responses from Anthropic and run your tools until a full response is generated. **Unlike with `openai-functions`,** all messages are returned, since Claude tends to generate meaningful context before calling the tool. The messages aren't limited to strings either, so be careful when interpreting the response.

```python
generated_message = conversation.run_until_response()
further_comment = conversation.run_until_response(max_tokens=4096)
```

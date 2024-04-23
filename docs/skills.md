# Skills

A skill allows you to combine several tools into one object, generate schemas for all of them at once, and then call the tool the AI requests. The most basic skill is defined with a [BasicToolSet](anthropic_tools.BasicToolSet) - it is just a container for other tools. Here's an example of its usage:

```python
skill = BasicToolSet()

@skill.add_tool
def get_current_weather(location: str) -> dict:
    ...

@skill.add_tool(
    name="set_weather_but_for_real",
    description="Set the weather or something",
    save_return=True,
    serialize=False,
    interpret_as_response=True
)
def set_weather(location: str, weather_description: str):
   ...

schema = skill.tools_schema
```

The parameters here are:

- `name` - the overwritten function name, otherwise will default to the function name
- `description` - the overwritten function description sent to the AI - will use the description from the docstring by default
- `save_return` - whether to send the return value of the function back to the AI; some functions - mainly those that don't return anything - don't need to do this
- `serialize` - whether to serialize the function's return value before sending the result back to the AI; Anthropic expects a tool use result to be a string; if this is False, `str()` will run on the function return. Otherwise, it will use JSON serialization, so if `serialize` is set to True, the function return needs to be JSON-serializable. If interpret_as_response is set to True and serialize is set to False, the function should return the list of blocks that will be sent to the AI. The primary use case for this is when you want to send images to Claude as part of the function response - you can also return a lost of [`ToolOutput`](anthropic_tools.ToolOutput)s - they're handled separately, so that proper tool IDs are integrated into the response where possible.
- `interpret_as_response` - whether to interpret the return value of the function (the serialized one if `serialize` is set to True) as the response from the AI

`schema` will be a list of JSON objects ready to be sent to Anthropic. You can then call your tools directly with the response returned from Claude:

```python
weather = skill(
    {
        "id": "1234",
        "type": "tool_use",
        "name": "get_current_weather",
        "input": {
            "location": "San Francisco, CA",
            "unit": "FAHRENHEIT",
        },
    }
)
```

When invalid content is passed in for the arguments, the output not adhering to the schema, the tool will raise either [BrokenSchemaError](anthropic_tools.BrokenSchemaError).

## Union skills

A more advanced one is a [union skillset](anthropic_tools.UnionSkillSet) that combines others. It exposes one new method:

```python
union_skill.add_skill(skill)
```

It still supports everything a [BasicToolSet](anthropic_tools.BasicToolSet), though; it can have a few functions inherent to it while still combining the other skillsets.

**Note:** unlike in `openai-functions`, a togglable skillset is not yet supported - I don't quite know how to make it work with several function calls in one message.

## Developing your own

Skills are extensible; you can build your own by inheriting them from the [ToolSet](anthropic_tools.ToolSet) base class. You then have to provide these methods and properties:

- `tools_schema` - the schema of the tools; list of JSON objects
- `run_tool(input_data)` - that runs the tool and returns the result; takes in the raw `ToolUseBlock` or `ToolUseBlockParam` retrieved from Anthropic. Should raise [ToolNotFoundError](anthropic_tools.ToolNotFoundError) if there isn't a function with this name in the skillset, to allow for other skills to be queried.

You can also inherit from the [MutableToolSet](anthropic_tools.MutableToolSet), which greatly simplifies adding and removing functions from the skill. Then, you have to define two additional methods:

- `_add_tool(tool)` - adds an [AnthropicTool](anthropic_tools.AnthropicTool) to the skill
- `_remove_tool(name)` - takes in a string and deletes the tool with that name

Your skill will then have the `@skill.add_tool` decorator available.

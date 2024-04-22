# Introduction

The `anthropic-tools` library simplifies the usage of Anthropics's tool use feature. It abstracts away the complexity of parsing function signatures and docstrings by providing developers with a clean and intuitive interface. Once again, the library is a near-clone of my [openai-functions](https://openai-functions.readthedocs.io) library that does the same with OpenAI.

`anthropic-tools` takes care of the following tasks:

- Parsing the function signatures (with type annotations) and docstrings.
- Sending the conversation and tool descriptions to Anthropic Claude.
- Deciding whether to call a tool based on the model's response.
- Calling the appropriate function with the provided arguments.
- Updating the conversation with the tool response.
- Repeating the process until the model generates a user-facing message.

This abstraction allows developers to focus on defining their functions and adding user messages without worrying about the details of tool use.

# Quickstart

## Installation

You can install `anthropic-tools` from PyPI using pip:

```
pip install anthropic-tools
```

Unlike `openai-functions`, since Anthropic does not support forcing the model to generate a specific function call, the only way of using it is as an assistant with access to tools.

(your-first-conversation)=

## Your first conversation

The easiest way to use `anthropic-tools` is through the [conversation](conversation) interface. For that, you first import all of the necessary modules and create a client with your API key:

```python
import enum
import anthropic
from anthropic_tools import Conversation

client = anthropic.Anthropic(
    api_key="<YOUR_API_KEY>",
)
```

Then, we can create a [conversation](anthropic_tools.Conversation).

```python
conversation = Conversation(client)
```

A conversation contains our and the AI's messages, the tools we provide, and a set of methods for calling the AI with our tools. Now, we can add our tools to the conversation using the `@conversation.add_tool` decorator to make them available for the AI:

```python
class Unit(enum.Enum):
    FAHRENHEIT = "fahrenheit"
    CELSIUS = "celsius"

@conversation.add_tool
def get_current_weather(location: str, unit: Unit = Unit.FAHRENHEIT) -> dict:
    """Get the current weather in a given location.

    Args:
        location (str): The city and state, e.g., San Francisco, CA
        unit (Unit): The unit to use, e.g., fahrenheit or celsius
    """
    return {
        "location": location,
        "temperature": "72",
        "unit": unit.value,
        "forecast": ["sunny", "windy"],
    }
```

Note that the function _must_ have type annotations for all arguments, including extended type annotations for lists/dictionaries (for example, `list[int]` and not just `list`); otherwise the tool won't be able to generate a schema. Our conversation is now ready for tool use. The easiest way to do so is through the `conversation.ask` method. This method will repeatedly ask the AI for a response, running tools, until the AI responds with text to return:

```python
response = conversation.ask("What's the weather in San Francisco?")
# Should return three messages, the last one's content being something like:
# The current weather in San Francisco is 72 degrees Fahrenheit and it is sunny and windy.
```

The AI will probably (nobody can say for sure) then use the tool with `{"location": "San Francisco, CA"}`, which will get translated to `get_current_weather("San Francisco, CA")`. The function response will be serialized and sent back to the AI, and the AI will return a text description. You can read more about how to work with conversations [here](conversation).

## Just generating the schemas

If you want to generate the schemas, you can use a [ToolWrapper](anthropic_tools.ToolWrapper):

```python
from anthropic_tools import ToolWrapper

wrapper = ToolWrapper(get_current_weather)
schema = wrapper.schema
result = wrapper({"location": "San Francisco, CA"})
```

This creates an object that can both return you a schema of a tool and provide the function with properly parsed arguments. Another tool is a [ToolSet](anthropic_tools.BasicToolSet) that allows you to aggregate multiple tools into one schema:

```python
from anthropic_tools import BasicToolSet
import enum

skill = BasicToolSet()

class Unit(enum.Enum):
    FAHRENHEIT = "fahrenheit"
    CELSIUS = "celsius"

@skill.add_tool
def get_current_weather(location: str, unit: Unit = Unit.FAHRENHEIT) -> dict:
    """Get the current weather in a given location.

    Args:
        location (str): The city and state, e.g., San Francisco, CA
        unit (Unit): The unit to use, e.g., fahrenheit or celsius
    """
    return {
        "location": location,
        "temperature": "72",
        "unit": unit.value,
        "forecast": ["sunny", "windy"],
    }

@skill.add_tool
def set_weather(location: str, weather_description: str):
   ...

schema = skill.tools_schema
```

This then generates the schema for your tools.<details><summary>This is what `schema` looks like</summary>

```json
[
  {
    "name": "get_current_weather",
    "input_schema": {
      "type": "object",
      "properties": {
        "location": {
          "type": "string",
          "description": "The city and state, e.g., San Francisco, CA"
        },
        "unit": {
          "type": "string",
          "enum": ["FAHRENHEIT", "CELSIUS"],
          "description": "The unit to use, e.g., fahrenheit or celsius"
        }
      },
      "required": ["location"]
    },
    "description": "Get the current weather in a given location."
  },
  {
    "name": "set_weather",
    "input_schema": {
      "type": "object",
      "properties": {
        "location": {
          "type": "string"
        },
        "weather_description": {
          "type": "string"
        }
      },
      "required": ["location", "weather_description"]
    }
  }
]
```

</details>

You can now call the tools directly using the tool uses Anthropic returns:

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

This then calls the relevant function.<details><summary>`weather` is then just the raw return value of it, in this case:</summary>

```json
{
  "location": "San Francisco, CA",
  "temperature": "72",
  "unit": "fahrenheit",
  "forecast": ["sunny", "windy"]
}
```

</details>

You can read more about how to work with skills [here](skills).

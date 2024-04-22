# Anthropic tools

The `anthropic-tools` library simplifies the usage of Anthropics’s [tool use](https://docs.anthropic.com/claude/docs/tool-use) feature. It abstracts away the complexity of parsing function signatures and docstrings by providing developers with a clean and intuitive interface. It's a near-clone of my [openai-functions](https://openai-functions.readthedocs.io) library that does the same with OpenAI.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![PyPI version](https://badge.fury.io/py/anthropic-tools.svg)](https://badge.fury.io/py/anthropic-tools) [![Documentation Status](https://readthedocs.org/projects/anthropic-tools/badge/?version=latest)](https://anthropic-tools.readthedocs.io/en/latest/?badge=latest)

## Installation

You can install `anthropic-tools` from PyPI using pip:

```
pip install anthropic-tools
```

## Usage

1. Import the necessary modules and provide your API key:

```python
import enum
import anthropic
from anthropic_tools import Conversation

client = anthropic.Anthropic(
    api_key="<YOUR_API_KEY>",
)
```

2. Create a `Conversation` instance:

```python
conversation = Conversation(client)
```

3. Define your tools using the `@conversation.add_tool` decorator:

```python
class Unit(enum.Enum):
    FAHRENHEIT = "fahrenheit"
    CELSIUS = "celsius"

@conversation.add_tool()
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

4. Ask the AI a question:

```python
response = conversation.ask("What's the weather in San Francisco?")
# Should return three messages, the last one's content being something like:
# The current weather in San Francisco is 72 degrees Fahrenheit and it is sunny and windy.
```

You can read more about how to use `Conversation` [here](https://anthropic-tools.readthedocs.io/en/latest/conversation.html).

## More barebones use - just schema generation and result parsing:

```python
from anthropic_tools import ToolWrapper

wrapper = ToolWrapper(get_current_weather)
schema = wrapper.schema
result = wrapper({"location": "San Francisco, CA"})
```

Or you could use [skills](https://anthropic-tools.readthedocs.io/en/latest/skills.html).

## How it Works

`anthropic-tools` takes care of the following tasks:

- Parsing the function signatures (with type annotations) and docstrings.
- Sending the conversation and tool descriptions to Anthropic Claude.
- Deciding whether to call a tool based on the model's response.
- Calling the appropriate function with the provided arguments.
- Updating the conversation with the tool response.
- Repeating the process until the model generates a user-facing message.

This abstraction allows developers to focus on defining their functions and adding user messages without worrying about the details of tool use.

## Note

Please note that `anthropic-tools` is an unofficial project not maintained by Anthropic. Use it at your discretion.

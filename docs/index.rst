Welcome to anthropic-tools' documentation!
==========================================


The ``anthropic-tools`` library simplifies the usage of Anthropics's tool use feature. It abstracts away the complexity of parsing function signatures and docstrings by providing developers with a clean and intuitive interface.

This library is pretty much identical - this includes sharing a lot of code with - another one of my libraries, `openai-functions <https://openai-functions.readthedocs.io>`_. The ``openai-functions`` library is more powerful, but designed to work specifically with ChatGPT; this one is designed to work specifically with Anthropics's Claude. I designed it to be a drop-in replacement where possible. The documentation is also almost identical.

Where to start
--------------

Either way, you'll want to install ``anthropic-tools``:

.. code-block:: bash

   pip install anthropic-tools

Unlike ``openai-functions``, since Anthropic does not support forcing the model to generate a specific function call, the only way of using it is as an assistant with access to tools.

.. toctree::
   :maxdepth: 2
   :caption: Table of Contents:

   introduction
   conversation
   skills
   api
* :ref:`genindex`
* :ref:`search`

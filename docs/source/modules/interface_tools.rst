
``interface_tools``
===================

Not imported with ``pytrs`` by default.

.. code-block:: python

    import pytrs.interface_tools



``prompt_config()`` function for getting ``config`` settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This function launches a ``tkinter`` window to prompt the user for
desired ``config=`` with a GUI widget.

.. autofunction:: pytrs.interface_tools.prompt_config



``PromptConfig`` class for getting ``config`` settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This ``tkinter.Frame`` subclass can be incorporated into another
``tkinter`` application, to get desired ``config=`` settings from the
user with a GUI widget.

.. autoclass:: pytrs.interface_tools.PromptConfig
    :members:
    :special-members: __init__


``interface_tools``
===================

Not imported with ``pytrs`` by default.

.. code-block:: python

    import pytrs.interface_tools



``prompt_config()`` function for selecting ``config`` settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This function launches a ``tkinter`` window to prompt the user for
desired ``config=``, using a GUI widget.

.. autofunction:: pytrs.interface_tools.prompt_config


``prompt_attrib()`` function for selecting desired ``Tract`` attributes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This function launches a ``tkinter`` window to prompt the user for
which ``Tract`` attributes they would like, using a GUI widget.

.. autofunction:: pytrs.interface_tools.prompt_attrib


``PromptConfig`` class for selecting ``config`` settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This ``tkinter.Frame`` subclass can be incorporated into another
``tkinter`` application, to get desired ``config=`` settings from the
user with a GUI widget.

.. autoclass:: pytrs.interface_tools.PromptConfig
    :members:
    :special-members: __init__


``PromptAttrib`` class for selecting ``Tract`` attributes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This ``tkinter.Frame`` subclass can be incorporated into another
``tkinter`` application, to get desired ``Tract`` attributes from the
user with a GUI widget.

.. autoclass:: pytrs.interface_tools.PromptAttrib
    :members:
    :special-members: __init__

import sys
from typing import Callable, Union

import adsk.core
from .general_utils import handle_error


# Global Variable to hold Event Handlers
_handlers = []


def add_handler(
        event: adsk.core.Event,
        callback: Callable,
        *,
        name: str = None,
        local_handlers: list = None
):
    """Adds an event handler to the specified event.

    Arguments:
    event -- The event object you want to connect a handler to.
    callback -- The function that will handle the event.
    name -- A name to use in logging errors associated with this event.
            Otherwise the name of the event object is used. This argument
            must be specified by its keyword.
    local_handlers -- A list of handlers you manage that is used to maintain
                      a reference to the handlers so they aren't released.
                      This argument must be specified by its keyword. If not
                      specified the handler is added to a global list and can
                      be cleared using the clear_handlers function. You may want
                      to maintain your own handler list so it can be managed 
                      independently for each command.
    """   
    module = sys.modules[event.__module__]
    handler_type = module.__dict__[event.add.__annotations__['handler']]
    handler = _create_handler(handler_type, callback, event, name, local_handlers)
    event.add(handler)
    return handler


def clear_handlers():
    """Clears the global list of handlers.
    """
    global _handlers
    _handlers = []


def _create_handler(
        handler_type,
        callback: Callable,
        event: adsk.core.Event,
        name: str = None,
        local_handlers: list = None
):
    handler = _define_handler(handler_type, callback, name)()

    (local_handlers if local_handlers is not None else _handlers).append(handler)
    return handler


def _define_handler(handler_type, callback, name: str = None):
    name = name or handler_type.__name__

    class Handler(handler_type):
        def __init__(self):
            super().__init__()

        def notify(self, args):
            try:
                callback(args)
            except:
                handle_error(name)

    return Handler

# -*- coding: utf-8 -*-

from collections.abc import Callable
from functools import wraps
from inspect import getdoc

from deprecated.params import deprecated_params


class AuthenticationError(Exception):
    """Custom exception for authentication failures."""

    pass


def requires_auth(f):
    """Decorator for methods that need authentication"""

    @wraps(f)
    def wrapper(self, *args, **kwargs):
        # Get function parameter names (excluding 'self')
        import inspect

        sig = inspect.signature(f)
        param_names = list(sig.parameters.keys())[1:]  # Skip 'self'

        # Create a dictionary of all arguments (positional + keyword)
        bound_args = {}
        for i, arg in enumerate(args):
            if i < len(param_names):
                bound_args[param_names[i]] = arg
        bound_args.update(kwargs)

        # Check if client_id and client_secret are provided
        client_id = bound_args.get("client_id")
        client_secret = bound_args.get("client_secret")

        if f.__name__.startswith("mint"):
            # If client_id and client_secret are provided, we can use them
            if client_id is not None and client_secret is not None:
                # Credentials provided in function call, proceed
                return f(self, *args, **kwargs)
        if not self.auth.has_credentials():
            raise AuthenticationError(
                f"{f.__name__} requires authentication. Either provide `client_id` and `client_secret` OR `username` and `password`."
            )
        return f(self, *args, **kwargs)

    return wrapper


def has_deprecated_parameter(
    param_name: str,
    *,  # makes it so Python requires the following parameters to be specified as _kwargs_
    reason: str,
):
    """
    A decorator you can use to designate a parameter of the decorated function as being deprecated.

    This decorator is an enhanced variant of the `deprecated_params` decorator from the third-party
    `Deprecated` package. That decorator has a shortcoming, which is that it does not modify the
    Sphinx docs. This decorator _does_ modify the Sphinx docs.

    Decorating a given function with this decorator will cause the following two things to happen:

    1. Whenever the function is invoked with the deprecated parameter, Python will display a warning.
    2. The Sphinx documentation for the function will include a note about the deprecated parameter.
       Note: We use the `.. admonition::` directive rather than the `.. deprecated::` directive to
             add that note, because Sphinx displays the latter the same way as a deprecation message
             about the entire _function_, and we don't want to imply that the entire _function_ is
             deprecated. We use `.. admonition::` to achieve a distinct appearance.

    Parameters
    ----------
    param_name:
        Name of the deprecated parameter.
    reason:
        Explanation shown in the run-time warning and the Sphinx docs (e.g. "Use ``foo`` instead.").

    Returns
    -------
    Callable
        The decorator.
    """

    # Raise an exception if the parameter name is empty.
    param_name_sanitized = param_name.strip()
    if len(param_name_sanitized) < 1:
        raise ValueError("Parameter name cannot be empty.")

    # Strip any leading/trailing whitespace from the reason.
    reason_sanitized = reason.strip()

    def decorator(class_or_func: Callable) -> Callable:
        # If the decorated thing is a class, apply the third-party `deprecated_params` decorator to
        # its `__init__` method. Otherwise, apply that decorator to the function, itself.
        if isinstance(class_or_func, type):
            class_or_func.__init__ = deprecated_params(  # type: ignore[misc]
                param_name_sanitized, reason=reason_sanitized
            )(
                class_or_func.__init__  # type: ignore[misc]
            )
            decorated_class_or_func = class_or_func
        else:
            decorated_class_or_func = deprecated_params(  # type: ignore[assignment]
                param_name_sanitized, reason=reason_sanitized
            )(class_or_func)

        # Make the note for the Sphinx docs.
        sphinx_note_lines = [
            ".. admonition:: Deprecated parameter",
            "",
            f"   The ``{param_name_sanitized}`` parameter is deprecated.",
            f"   {reason_sanitized}" if len(reason_sanitized) > 0 else "",
        ]
        sphinx_note = "\n".join(sphinx_note_lines)

        # Augment the decorated function's or class's docstring with the Sphinx note.
        #
        # Note: We use `inspect.getdoc(x)` instead of `x.__doc__` because, unlike the latter, the
        #       former normalizes the indentation level of the docstring lines. This way, we don't
        #       have to indent our injected note to different levels for different docstrings.
        #       Reference: https://docs.python.org/3/library/inspect.html#inspect.getdoc
        #
        original_docstring = getdoc(decorated_class_or_func)
        if not isinstance(original_docstring, str):
            original_docstring = ""
        decorated_class_or_func.__doc__ = (
            original_docstring.rstrip() + "\n\n\n" + sphinx_note + "\n"
        )

        # Return the decorated function, which is now decorated with the third-party `deprecated_params`
        # decorator _and_ has the augmented docstring.
        return decorated_class_or_func

    return decorator

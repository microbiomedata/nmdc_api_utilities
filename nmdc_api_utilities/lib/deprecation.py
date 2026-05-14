# -*- coding: utf-8 -*-
"""
This module "abstracts away" the complex import logic of the `deprecated` decorator; providing
developers with a simplified way of getting access to the decorator.
"""

import warnings
from functools import wraps
from sys import version_info
from typing import Any, Callable, ParamSpec, TypeVar

# If this script is being executed via Python 3.13 or newer, import the `deprecated` decorator from
# the standard library (it was introduced there in Python 3.13); otherwise, import it from the
# `typing_extensions` package (which provides "backports" of new Python features).
if version_info >= (3, 13):
    from warnings import deprecated  # type: ignore[attr-defined]
else:
    from typing_extensions import deprecated


# Define a couple "type variables" that help with type hinting for decorator definitions.
#
# From the docs: "Type variables exist primarily for the benefit of static type checkers."
#
# References:
# - https://docs.python.org/3/library/typing.html#typing.ParamSpec
# - https://docs.python.org/3/library/typing.html#typing.TypeVar
#
P = ParamSpec("P")
R = TypeVar("R")


def _append_deprecation_message(docstring: str | None, message: str) -> str:
    """
    Append a deprecation message to a docstring.

    Note: We use the `.. admonition::` directive rather than the `.. deprecated::` directive
          because Sphinx displays the latter the same way as a deprecation message about
          the entire _function_, and we don't want to imply that the entire _function_ has been
          deprecated. So, we use a distinct directive to give our message a distinct appearance.

    Reference: https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-admonition

    >>> _append_deprecation_message(
    ...     docstring="Some docstring.",
    ...     message="Some message."
    ... )
    'Some docstring.\\n\\n.. admonition:: Deprecated parameter\\n\\n   Some message.'
    """

    if not isinstance(docstring, str):
        docstring = ""

    admonition = f".. admonition:: Deprecated parameter\n\n   {message}"
    return f"{docstring}\n\n{admonition}"


# Implement a custom decorator that supports the deprecation of individual function parameters and
# allows the caller to specify a `stacklevel`.
#
# Note: The reason we didn't use the third-party `Deprecated` package for this is that, for parameter
#       deprecation, it doesn't allow the caller to specify a `stacklevel`. As a trade-off, we have
#       to handle the injection of Sphinx directive into docstrings ourselves.
#
def has_deprecated_parameter(
    parameter_name: str,
    stacklevel: int = 2,
    footnote: str = "",
):
    """
    A decorator that can be used to decorate a function (or a class) in order to indicate that a
    specific _parameter_ of that function (or of that class's `__init__` method) is deprecated.

    When the decorated function is invoked (or class is initialized), a warning will be displayed.
    Also, the Sphinx documentation about that function (or class) will include that same warning.

    Parameters
    ----------
    parameter_name
        The name of the parameter that is deprecated
    stacklevel
        How many layers up the "call stack" the user-controlled offending code is
    footnote
        An optional footnote to append to the warning message (e.g. "Use foo instead.")

    Returns
    -------
    Callable
        A decorator that can be applied to a function or class
    """

    # Build the message we will both inject into the docstring and display on the console.
    message = f"The ``{parameter_name}`` parameter is deprecated."
    if len(footnote.strip()) > 0:
        message = f"{message} {footnote.strip()}"

    def apply_wrapper(subject_function: Callable[P, R]) -> Callable[P, R]:
        """
        Wraps the subject function in an "outer" function that checks whether the deprecated
        parameter is being used and, if so, displays a message on the console.
        """

        @wraps(subject_function)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            """
            The "outer" function that checks whether the deprecated parameter is being used and,
            if so, displays a message on the console.
            """
            if parameter_name in kwargs:
                warnings.warn(message, DeprecationWarning, stacklevel=stacklevel)
            return subject_function(*args, **kwargs)

        return wrapper

    def decorate(subject_function_or_class: Any) -> Any:
        # If the subject is a class, wrap the class's `__init__` method (not the class, itself) and
        # modify the class's docstring. Otherwise, (i.e. if the subject is a function), wrap the
        # function and modify its docstring.
        subject_function_or_class.__doc__ = _append_deprecation_message(
            docstring=subject_function_or_class.__doc__,
            message=message,
        )
        if isinstance(subject_function_or_class, type):
            subject_function_or_class.__init__ = apply_wrapper(
                subject_function_or_class.__init__
            )
            return subject_function_or_class
        else:
            return apply_wrapper(subject_function_or_class)

    return decorate

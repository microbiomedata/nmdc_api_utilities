# -*- coding: utf-8 -*-
# file to hold decorators
from functools import wraps


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

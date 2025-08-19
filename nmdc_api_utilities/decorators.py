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
        if not self.auth.has_credentials():
            raise AuthenticationError(
                f"{f.__name__} requires authentication. Either provide `client_id` and `client_secret` or `username` and `password`."
            )
        return f(self, *args, **kwargs)

    return wrapper

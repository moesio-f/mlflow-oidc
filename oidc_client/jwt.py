"""Simple JWT decoder using
Base64Url.
"""

import base64
import json

from pydantic import BaseModel


class Jwt(BaseModel):
    """Representation of a JWT.

    :param header: decoded header.
    :param payload: decoded payload.
    :param signature: encoded signature. Client
        doesn't support signature decoding.
    :param encoded: complete JWT as encoded
        string.
    """

    header: dict
    payload: dict
    signature: str
    encoded: str

    @classmethod
    def decode(cls, value: str) -> "Jwt":
        """Decode a JWT.

        :param value: encoded jwt.
        :return: decoded jwt.
        """

        parts = [v for v in value.split(".")]
        n = len(parts)
        assert n == 3, f"Invalid JWT. Expected 3 parts got {n} instead."
        data = dict(encoded=value, signature=parts[-1])
        for key, value in zip(["header", "payload"], parts[:-1]):
            data[key] = json.loads(
                base64.urlsafe_b64decode(value.encode() + b"==").decode()
            )
        return cls(**data)

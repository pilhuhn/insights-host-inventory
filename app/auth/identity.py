import os
from base64 import b64decode
from json import loads

from app.logging import get_logger
from app.logging import threadctx


__all__ = ["Identity", "from_auth_header", "from_bearer_token", "validate"]

logger = get_logger(__name__)

SHARED_SECRET_ENV_VAR = "INVENTORY_SHARED_SECRET"


def from_auth_header(base64):
    json = b64decode(base64)
    identity_dict = loads(json)
    return Identity(identity_dict["identity"]["account_number"], identity_dict["identity"]["type"])


def from_bearer_token(token):
    return Identity(token=token)


class Identity:
    def __init__(self, account_number=None, identity_type=None, token=None):
        """
        A "trusted" identity is trusted to be passing in
        the correct account number(s).
        """
        if not account_number and not token:
            raise ValueError("Neither the account_number or token has been set")

        self.is_trusted_system = False
        self.account_number = account_number
        self.identity_type = identity_type

        threadctx.account_number = account_number

        if token:
            self.token = token
            self.is_trusted_system = True
            threadctx.account_number = "<<TRUSTED IDENTITY>>"

    def _asdict(self):
        return {"account_number": self.account_number, "type": self.identity_type}

    def __eq__(self, other):
        return self.account_number == other.account_number


def validate(identity):
    if identity.is_trusted_system:
        # This needs to be moved.
        # The logic for reading the environment variable and logging
        # a warning should go into the Config class
        shared_secret = os.getenv(SHARED_SECRET_ENV_VAR)
        if not shared_secret:
            logger.warning("%s environment variable is not set", SHARED_SECRET_ENV_VAR)
        if identity.token != shared_secret:
            raise ValueError("Invalid credentials")
    else:
        # Ensure the account number is present.
        if not identity.account_number:
            raise ValueError("The account_number is mandatory.")

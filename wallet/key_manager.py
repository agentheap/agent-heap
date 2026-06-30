import os

from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware


class KeyManager:
    def __init__(self, rpc_url: str):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        private_key = os.getenv("PRIVATE_KEY")
        if private_key:
            self.account = self.w3.eth.account.from_key(private_key)
        else:
            self.account = None

    @property
    def address(self) -> str | None:
        return self.account.address if self.account else None

    def is_connected(self) -> bool:
        return self.w3.is_connected()

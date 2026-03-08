from typing import Self

from common.infrastructure.config.qdrant_config import QdrantConfig
from qdrant_client import AsyncQdrantClient


class QdrantStore:
    def __init__(self, client: AsyncQdrantClient, config: QdrantConfig):
        self._client = client
        self._config = config

    @classmethod
    def create(cls, config: QdrantConfig) -> Self:
        client = cls.create_client(config)
        return cls(client=client, config=config)

    @staticmethod
    def create_client(config: QdrantConfig) -> AsyncQdrantClient:
        return AsyncQdrantClient(config.endpoint_url, api_key=config.secret_key)

    def get_config(self) -> QdrantConfig:
        return self._config

    def get_client(self) -> AsyncQdrantClient:
        return self._client

    async def shutdown(self) -> None:
        await self._client.close(self._config.shutdown_grace)

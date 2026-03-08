"""Application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from bootstrap.config import AppConfig
from bootstrap.utils import log_config
from common.infrastructure.database.sqlalchemy.database import Database
from common.infrastructure.di.container.common import CommonContainer
from common.infrastructure.logger.logging.logger_factory import LoggerFactory
from common.infrastructure.queues.faststream.utils import create_rabbit
from common.infrastructure.storage.minio.storage import MinioStorage
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from filetype.types import document
from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from luminary_files.application.interfaces.services.file_service import IFileService
from luminary_files.infrastructure.di.container import FileContainer

from luminary.content.infrastructure.di.container import ContentContainer
from luminary.model.infrastructure.di.container import ModelContainer
from luminary.model.infrastructure.services.llama_index.client import MappedOpenAI
from luminary.source.application.interfaces.usecases.command.create_source_use_case import (
    ICreateFileSourceUseCase,
)
from luminary.source.infrastructure.di.container import SourceContainer


def main() -> FastAPI:
    """Initialize and bootstrap the application.

    Returns:
        Configured App instance.

    """
    # Load configuration
    config = AppConfig.load()

    # Logger
    logger = LoggerFactory.create(None, config.env, config.logger)
    logger.info("logger initialized")

    log_config(logger, config)

    # Database
    logger.info("initializing database...")
    database = Database.create(config.db, logger)
    logger.info("database initialized")

    # MinIO
    logger.info("initializing MinIO storage...")
    storage = MinioStorage.create(config.s3)
    logger.info("MinIO storage initialized")

    # RabbitMQ
    logger.info("initializing broker...")
    broker = create_rabbit(config.rabbit)
    logger.info("broker initialized")

    # Vector store
    logger.info("initializing vector store...")
    docs = SimpleDirectoryReader("./data").load_data()
    storage_context = StorageContext.from_defaults(vector_store=SimpleVectorStore())
    vector_store_index = VectorStoreIndex.from_documents(
        docs, storage_context=storage_context
    )
    logger.info("vector store initialized")

    # LLM
    llm = MappedOpenAI(
        model=config.llm.model,
        api_key=config.llm.api_key,
        api_base=config.llm.base_url,
        temperature=0.3,
    )
    MappedOpenAI.override(config.llm.model, config.llm.provider_model)
    logger.info("llm initialized")

    # Embedding Model
    embed_model = OpenAIEmbedding(
        api_key=config.llm.api_key, api_base=config.llm.base_url
    )
    logger.info("embedding model initialized")

    # Create FastAPI server
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
        logger.info("application ready to accept requests")
        yield
        logger.info("application shutdown begins")
        await database.shutdown()

    server = FastAPI(lifespan=lifespan)

    # Bootstrap common container with config and database
    common_container = CommonContainer(
        config=config, logger=logger, database=database, storage=storage, broker=broker
    )

    uuid_generator = common_container.uuid_generator
    query_executor = common_container.query_executor
    clock = common_container.clock
    event_bus = common_container.event_bus

    file_container = FileContainer(
        clock=clock,
        uuid_generator=uuid_generator,
        query_executor=query_executor,
        storage=storage,
        allowed_mime_types={"text/plain", "text/markdown", document.Docx.MIME},
    )

    content_container = ContentContainer(
        clock=clock,
        uuid_generator=uuid_generator,
        query_executor=query_executor,
        storage=storage,
        file_content_extractor=None,  # NOTE: Has to be overriden later
    )

    content_storage = content_container.content_storage

    model_container = ModelContainer(
        content_storage=content_storage,
        vector_store_index=vector_store_index,
        embed_model=embed_model,
    )

    content_container.file_content_extractor.override(model_container.content_extractor)

    source_container = SourceContainer(
        clock=clock,
        uuid_generator=uuid_generator,
        query_executor=query_executor,
    )

    # Register routes

    server.dependency_overrides[IFileService] = lambda: file_container.file_service()
    server.dependency_overrides[ICreateFileSourceUseCase] = (
        lambda: source_container.create_file_source_use_case()
    )

    server.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8081", config.deploy.external_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Create and configure app
    return server


app = main()
if __name__ == "__main__":
    pass

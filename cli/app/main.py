"""Application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from bootstrap.config import AppConfig
from bootstrap.utils import log_config
from common.infrastructure.database.sqlalchemy.database import Database
from common.infrastructure.di.container.common import CommonContainer
from common.infrastructure.logger.logging.logger_factory import LoggerFactory
from common.infrastructure.queues.faststream.utils import create_rabbit
from common.infrastructure.storage.minio.client import MinioStorage
from common.infrastructure.storage.qdrant.client import QdrantStore
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from filetype.types import document
from llama_index.core import Settings, VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from luminary_files.application.interfaces.services.file_service import IFileService
from luminary_files.infrastructure.di.container import FileContainer

from luminary.content.infrastructure.di.container import ContentContainer
from luminary.model.infrastructure.di.container import ModelContainer
from luminary.model.infrastructure.services.llama_index.client import MappedOpenAI
from luminary.source.application.interfaces.usecases.command.create_source_use_case import (
    ICreateFileSourceUseCase,
    ICreateLinkSourceUseCase,
    ICreatePageSourceUseCase,
)
from luminary.source.infrastructure.di.container import SourceContainer
from luminary.source.presentation.http.fastapi.controllers import (
    command_router as source_command_router,
)


FILES_BUCKET = "files"
CONTENT_BUCKET = "content"

# Load configuration
config = AppConfig.load()

# Logger
logger = LoggerFactory.create(None, config.env, config.logger)
logger.info("logger initialized")

log_config(logger, config)


def main() -> FastAPI:
    """Initialize and bootstrap the application.

    Returns:
        Configured App instance.

    """
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

    Settings.llm, Settings.embed_model = llm, embed_model

    # Vector store
    logger.info("initializing vector store...")

    qdrant_store = QdrantStore.create(config.qdrant)
    vector_store = QdrantVectorStore(
        collection_name=config.qdrant.collection_name, aclient=qdrant_store.get_client()
    )
    vector_store_index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

    logger.info("vector store initialized")

    # Create FastAPI server
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
        logger.info("application ready to accept requests")
        await broker.start()
        await storage.ensure_bucket()
        await storage.ensure_bucket(FILES_BUCKET)
        await storage.ensure_bucket(CONTENT_BUCKET)

        yield
        logger.info("application shutdown begins")
        await broker.stop()
        await database.shutdown()
        await storage.shutdown()
        await qdrant_store.shutdown()

    server = FastAPI(lifespan=lifespan)

    # Bootstrap common container with config and database
    common_container = CommonContainer(
        config=config, logger=logger, database=database, storage=storage, broker=broker
    )

    uuid_generator = common_container.uuid_generator
    query_executor = common_container.query_executor
    clock = common_container.clock
    unit_of_work = common_container.unit_of_work
    event_bus = common_container.event_bus

    file_container = FileContainer(
        bucket_name=FILES_BUCKET,
        clock=clock,
        uuid_generator=uuid_generator,
        query_executor=query_executor,
        storage=storage.get_client(),
        allowed_mime_types={"text/plain", "text/markdown", document.Docx.MIME},
    )

    file_type_introspector = file_container.file_type_introspector

    content_container = ContentContainer(
        bucket_name=CONTENT_BUCKET,
        clock=clock,
        uuid_generator=uuid_generator,
        query_executor=query_executor,
        storage=storage.get_client(),
        file_content_extractor=None,  # NOTE: Has to be overriden later
    )

    content_service = content_container.content_service
    content_storage = content_container.content_storage

    model_container = ModelContainer(
        content_storage=content_storage,
        vector_store_index=vector_store_index,
        embed_model=embed_model,
        file_type_introspector=file_type_introspector,
    )

    content_container.file_content_extractor.override(model_container.content_extractor)

    source_container = SourceContainer(
        clock=clock,
        uuid_generator=uuid_generator,
        query_executor=query_executor,
        unit_of_work=unit_of_work,
        event_bus=event_bus,
        content_service=content_service,
    )

    # Register routes
    server.dependency_overrides[IFileService] = lambda: file_container.file_service()
    server.dependency_overrides[ICreateFileSourceUseCase] = (
        lambda: source_container.create_file_source_use_case()
    )
    server.dependency_overrides[ICreatePageSourceUseCase] = (
        lambda: source_container.create_page_source_use_case()
    )
    server.dependency_overrides[ICreateLinkSourceUseCase] = (
        lambda: source_container.create_link_source_use_case()
    )

    server.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    router = APIRouter()
    router.include_router(source_command_router, prefix="/sources")

    server.include_router(router, prefix="/api/v1")

    return server


app = main()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

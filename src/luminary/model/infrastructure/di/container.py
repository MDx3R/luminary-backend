"""Model bounded context DI container."""

from typing import Any

from dependency_injector import containers, providers
from llama_index.readers.file import UnstructuredReader

from luminary.model.application.services.embedding_service import EmbeddingService
from luminary.model.infrastructure.services.llama_index.engine import (
    LlamaIndexEngine,
)
from luminary.model.infrastructure.services.llama_index.file_content_extractor import (
    LlamaIndexFileContentExtractor,
)
from luminary.model.infrastructure.services.llama_index.vector_store import (
    LlamaIndexVectorStore,
)


class ModelContainer(containers.DeclarativeContainer):
    """Dependency injection container for model bounded context."""

    # Explicit dependency declarations

    vector_store_index: providers.Dependency[Any] = providers.Dependency()
    embed_model: providers.Dependency[Any] = providers.Dependency()
    llm: providers.Dependency[Any] = providers.Dependency()

    file_type_introspector: providers.Dependency[Any] = providers.Dependency()

    # Storage
    vector_store = providers.Singleton(
        LlamaIndexVectorStore,
        index=vector_store_index,
        embed_model=embed_model,
    )

    # Services
    content_extractor = providers.Singleton(
        LlamaIndexFileContentExtractor,
        reader=UnstructuredReader(),
        file_introspector=file_type_introspector,
    )
    embedding_service = providers.Singleton(EmbeddingService, vector_store=vector_store)

    inference_engine = providers.Singleton(
        LlamaIndexEngine,
        llm=llm,
        index=vector_store_index,
        similarity_top_k=5,
        similarity_cutoff=0.7,
    )

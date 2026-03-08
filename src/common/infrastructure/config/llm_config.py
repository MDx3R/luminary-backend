from typing import Self

from pydantic import BaseModel, model_validator


class LLMConfig(BaseModel):
    model: str
    provider_model: str = ""
    base_url: str
    api_key: str | None = None

    @model_validator(mode="after")
    def default_provider_model(self) -> Self:
        if not self.provider_model:
            self.provider_model = self.model

        return self

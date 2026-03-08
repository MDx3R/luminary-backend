from typing import Any, ClassVar

from llama_index.llms.openai import OpenAI


class MappedOpenAI(OpenAI):
    """MappedOpenAI overrides logic for building model request kwargs.

    Some OpenAI-compatible providers add prefixes to model identifiers, which
    doesn't work correctly with LlamaIndex. This class maps model names to their
    correct identifiers.
    """

    MODEL_MAP: ClassVar = {
        "gpt-5-nano": "openai/gpt-5-nano",
        "gpt-5-mini": "openai/gpt-5-mini",
        "gpt-5": "openai/gpt-5",
    }

    def _get_model_kwargs(self, **kwargs: Any) -> dict[str, Any]:
        result = super()._get_model_kwargs(**kwargs)

        model = result.get("model", self.model)
        if model in self.MODEL_MAP:
            result["model"] = self.MODEL_MAP[model]

        return result

    @classmethod
    def override(cls, key: str, value: str) -> None:
        cls.MODEL_MAP[key] = value

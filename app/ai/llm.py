from litellm import acompletion

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

LLM_MODELS = [
    settings.gemini_model,
    settings.groq_model,
]


async def generate_answer(prompt: str) -> str:
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty")

    last_error: Exception | None = None

    for model in LLM_MODELS:
        try:
            response = await acompletion(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.1,
            )

            answer = response.choices[0].message.content

            if not answer or not answer.strip():
                raise RuntimeError(
                    f"{model} returned an empty response"
                )

            return answer.strip()

        except Exception as error:
            last_error = error

            logger.warning(
                "LLM model %s failed: %s",
                model,
                error,
            )

    raise RuntimeError(
        "All configured LLM models failed"
    ) from last_error
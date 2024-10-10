import urllib.parse

import aiohttp
import bittensor as bt
import pydantic
from common.protocol import SubmitResults
from pydantic import BaseModel, Field


class ValidationResponse(BaseModel):
    score: float
    preview: str | None = Field(default=None, description="Optional. Preview image, base64 encoded PNG")


async def validate(endpoint: str, synapse: SubmitResults) -> ValidationResponse | None:
    prompt = synapse.task.prompt  # type: ignore[union-attr]
    data = synapse.results
    validate_url = urllib.parse.urljoin(endpoint, "/validate_ply/")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(validate_url, json={"prompt": prompt, "data": data}) as response:
                if response.status == 200:
                    data_dict = await response.json()
                    results = ValidationResponse(**data_dict)
                    bt.logging.debug(f"Validation score: {results.score:.2f} | Prompt: {prompt}")
                    return results
                else:
                    bt.logging.error(f"Validation failed: [{response.status}] {response.reason}")
        except aiohttp.ClientConnectorError:
            bt.logging.error(f"Failed to connect to the endpoint. The endpoint might be inaccessible: {endpoint}.")
        except TimeoutError:
            bt.logging.error(f"The request to the endpoint timed out: {endpoint}")
        except aiohttp.ClientError as e:
            bt.logging.error(f"An unexpected client error occurred: {e} ({endpoint})")
        except pydantic.ValidationError as e:
            bt.logging.error(f"Incompatible validation response format: {e} ({endpoint})")
        except Exception as e:
            bt.logging.error(f"An unexpected error occurred: {e} ({endpoint})")

    return None


async def version(endpoint: str) -> str:
    version_url = urllib.parse.urljoin(endpoint, "/version/")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(version_url) as response:
                if response.status == 200:
                    endpoint_version = await response.text()
                    bt.logging.debug(f"Validation endpoint version: {endpoint_version}")
                    return endpoint_version
                else:
                    bt.logging.error(f"Validation failed with code: {response.status}")
                    return f"{response.status}:{response.reason}"
        except aiohttp.ClientConnectorError:
            bt.logging.error(f"Failed to connect to the endpoint. The endpoint might be inaccessible: {endpoint}.")
            return "can't reach endpoint"
        except TimeoutError:
            bt.logging.error(f"The request to the endpoint timed out: {endpoint}")
            return "request timeout"
        except aiohttp.ClientError as e:
            bt.logging.error(f"An unexpected client error occurred: {e} ({endpoint})")
            return "unexpected error"
        except Exception as e:
            bt.logging.error(f"An unexpected error occurred: {e} ({endpoint})")

    return "unexpected error"

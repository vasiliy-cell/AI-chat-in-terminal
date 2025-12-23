import aiohttp
import json
from lib import load_api_key, ConfigError
from errors import APIError

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"


async def stream_request(user_request: str):
    """Async generator yielding chunks of assistant text."""
    api_key = load_api_key()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "deepseek-chat",
        "stream": True,
        "messages": [{"role": "user", "content": user_request}],
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                DEEPSEEK_URL,
                headers=headers,
                json=payload,
                timeout=None,
            ) as response:

                if response.status != 200:
                    text = await response.text()
                    raise APIError(f"HTTP {response.status}: {text}")

                async for line in response.content:
                    line = line.decode("utf-8").strip()

                    if not line or not line.startswith("data:"):
                        continue

                    data = line.removeprefix("data: ").strip()

                    if data == "[DONE]":
                        break

                    chunk = json.loads(data)
                    delta = chunk["choices"][0]["delta"]

                    if "content" in delta:
                        yield delta["content"]

    except aiohttp.ClientError as e:
        raise APIError(f"Streaming failed: {e}") from e
    except (KeyError, json.JSONDecodeError) as e:
        raise APIError("Invalid streaming response") from e
    except ConfigError as e:
        raise APIError(f"Config error: {e}") from e

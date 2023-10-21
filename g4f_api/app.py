import json
import random
import string
import time
from typing import Any

import g4f
from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import StreamingResponse
from g4f import ChatCompletion
from loguru import logger
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(GZipMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chat/completions")
@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    req_data = await request.json()
    stream = req_data.get("stream", False)
    model = req_data.get("model", "gpt-3.5-turbo")
    messages = req_data.get("messages")
    temperature = req_data.get("temperature", 1.0)
    top_p = req_data.get("top_p", 1.0)
    max_tokens = req_data.get("max_tokens", 4096)

    logger.info(f"chat_completions: {req_data}, stream: {stream}, model: {model}, messages: {messages}, temperature: {temperature}, top_p: {top_p}, max_tokens: {max_tokens}")

    response = ChatCompletion.create(
        model=model,
        stream=stream,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        system_prompt="",
    )

    completion_id = "".join(random.choices(string.ascii_letters + string.digits, k=28))
    completion_timestamp = int(time.time())

    if not stream:
        return {
            "id": f"chatcmpl-{completion_id}",
            "object": "chat.completion",
            "created": completion_timestamp,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response,
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": None,
                "completion_tokens": None,
                "total_tokens": None,
            },
        }

    def streaming():
        for chunk in response:
            completion_data = {
                "id": f"chatcmpl-{completion_id}",
                "object": "chat.completion.chunk",
                "created": completion_timestamp,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "content": chunk,
                        },
                        "finish_reason": None,
                    }
                ],
            }

            content = json.dumps(completion_data, separators=(",", ":"))
            yield f"data: {content}\n\n"
            time.sleep(0.1)

        end_completion_data: dict[str, Any] = {
            "id": f"chatcmpl-{completion_id}",
            "object": "chat.completion.chunk",
            "created": completion_timestamp,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop",
                }
            ],
        }
        content = json.dumps(end_completion_data, separators=(",", ":"))
        yield f"data: {content}\n\n"

    return StreamingResponse(streaming(), media_type="text/event-stream")


@app.post("/v1/completions")
async def completions(request: Request):
    req_data = await request.json()
    req_data.get("model", "text-davinci-003")
    prompt = req_data.get("prompt")
    req_data.get("messages")
    temperature = req_data.get("temperature", 1.0)
    top_p = req_data.get("top_p", 1.0)
    max_tokens = req_data.get("max_tokens", 4096)

    response = g4f.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
    )

    completion_id = "".join(random.choices(string.ascii_letters + string.digits, k=24))
    completion_timestamp = int(time.time())

    return {
        "id": f"cmpl-{completion_id}",
        "object": "text_completion",
        "created": completion_timestamp,
        "model": "text-davinci-003",
        "choices": [
            {"text": response, "index": 0, "logprobs": None, "finish_reason": "length"}
        ],
        "usage": {
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
        },
    }


import json
import sys
import traceback

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent import make_client
from agent.react_loop import stream_react_agent

try:
    make_client()
except RuntimeError as exc:
    print(f"Startup error: {exc}", file=sys.stderr)
    sys.exit(1)

app = FastAPI(title="Store Assistant Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",   # disables nginx buffering
    "Connection": "keep-alive",
}


class QueryRequest(BaseModel):
    query: str


@app.post("/api/query")
async def query_agent(body: QueryRequest):
    def generate():
        try:
            for event in stream_react_agent(body.query.strip()):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception:
            err = traceback.format_exc()
            yield f"data: {json.dumps({'type': 'final', 'answer': f'Server error: {err}', 'tools_called': [], 'api_calls': 0})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream", headers=SSE_HEADERS)


@app.get("/api/health")
async def health():
    return {"status": "ok"}

# app.py
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional
import uvicorn
import asyncio
import time

app = FastAPI(title="Tiny MCP (HTTP)")

class JSONRPCRequest(BaseModel):
    jsonrpc: str
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[Any] = None

# Simple capability registry: map method names -> async functions
capability_registry = {}

def capability(name):
    def decorator(fn):
        capability_registry[name] = fn
        return fn
    return decorator

@capability("ping")
async def ping_handler(params):
    # tiny example: echo + server timestamp
    return {"echo": params, "server_time": time.time()}

@capability("sleep_then_echo")
async def sleep_then_echo(params):
    # example of an async capability (simulates I/O)
    delay = float(params.get("delay", 0.1))
    await asyncio.sleep(delay)
    return {"ok": True, "delay": delay, "received": params}

@app.post("/rpc")
async def rpc_endpoint(req: Request):
    payload = await req.json()
    try:
        reqobj = JSONRPCRequest(**payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"invalid JSON-RPC: {e}")

    # Basic JSON-RPC validation (very small)
    if reqobj.jsonrpc != "2.0":
        return {"jsonrpc": "2.0", "id": reqobj.id, "error": {"code": -32600, "message": "invalid jsonrpc version"}}

    handler = capability_registry.get(reqobj.method)
    if handler is None:
        return {"jsonrpc": "2.0", "id": reqobj.id, "error": {"code": -32601, "message": "Method not found"}}

    try:
        result = await handler(reqobj.params or {})
        return {"jsonrpc": "2.0", "id": reqobj.id, "result": result}
    except Exception as e:
        return {"jsonrpc": "2.0", "id": reqobj.id, "error": {"code": -32000, "message": f"Server error: {e}"}}

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

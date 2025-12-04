# backend/gateway/ws_gateway.py
import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# --- Optional gRPC control: guarded so /rpc never crashes ---
try:
    import grpc  # type: ignore
    from backend.grpc_stubs import training_pb2, training_pb2_grpc  # type: ignore
    HAS_CONTROL = hasattr(training_pb2_grpc, "TrainingControlStub")
    stub = (
        training_pb2_grpc.TrainingControlStub(grpc.insecure_channel("localhost:50051"))
        if HAS_CONTROL else None
    )
except Exception:
    training_pb2 = None  # type: ignore
    training_pb2_grpc = None  # type: ignore
    grpc = None  # type: ignore
    HAS_CONTROL = False
    stub = None

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- WebSocket fanout (in-memory broadcaster) ---
clients: set[WebSocket] = set()

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            msg = await ws.receive_text()
            try:
                data = json.loads(msg)
                if data.get("type") == "ping":
                    await ws.send_text(json.dumps({"type": "pong"}))
                    continue
            except Exception:
                # ignore non-JSON messages
                continue
            # rebroadcast trainer messages to other clients
            dead = []
            for c in clients:
                if c is ws:  # don't echo to sender
                    continue
                try:
                    await c.send_text(msg)
                except Exception:
                    dead.append(c)
            for d in dead:
                clients.discard(d)
    except WebSocketDisconnect:
        pass
    finally:
        clients.discard(ws)

async def publish(obj: dict):
    data = json.dumps(obj)
    dead = []
    for c in clients:
        try:
            await c.send_text(data)
        except Exception:
            dead.append(c)
    for d in dead:
        clients.discard(d)

# --- HTTP publish endpoint (trainer/demo posts here) ---
@app.post("/publish")
async def http_publish(obj: dict = Body(...)):
    if not isinstance(obj, dict) or "type" not in obj:
        return JSONResponse({"ok": False, "error": "invalid payload"}, status_code=400)
    await publish(obj)
    return {"ok": True}

# --- /rpc always responds; if no gRPC control, it broadcasts a control event ---
@app.post("/rpc")
async def rpc_bridge(cmd: dict):
    try:
        if HAS_CONTROL and stub is not None:
            t = cmd.get("type")
            if t == "pause":
                stub.Pause(training_pb2.Empty())  # type: ignore
                return {"ok": True}
            if t == "resume":
                stub.Resume(training_pb2.Empty())  # type: ignore
                return {"ok": True}
            if t == "delay":
                ms = int(cmd.get("ms", 0))
                stub.SetDelay(training_pb2.Delay(ms=ms))  # type: ignore
                return {"ok": True}
            return JSONResponse({"ok": False, "error": "unknown command"}, status_code=400)
        # Fallback: no gRPC control available — broadcast control so trainer can react
        await publish({"type": "control", "payload": cmd})
        return JSONResponse(
            {"ok": False, "error": "TrainingControl not available; command broadcast only"},
            status_code=501,
        )
    except Exception as e:
        # Never crash — surface error with 500 and text
        return JSONResponse({"ok": False, "error": f"rpc failure: {e}"}, status_code=500)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
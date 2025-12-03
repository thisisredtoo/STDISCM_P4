import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import uvicorn
import json
import grpc
from backend.grpc_stubs import training_pb2, training_pb2_grpc

app = FastAPI()

# --- WebSocket fanout (very small in-memory broadcaster) ---
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
      except Exception:
        pass
  except WebSocketDisconnect:
    pass
  finally:
    clients.discard(ws)

# Helper to publish to all clients from other parts of your app
async def publish(obj: dict):
  data = json.dumps(obj)
  dead = []
  for c in clients:
    try:
      await c.send_text(data)
    except Exception:
      dead.append(c)
  for d in dead: clients.discard(d)

# --- RPC bridge to trainer control service ---
channel = grpc.insecure_channel("localhost:50051")
stub = training_pb2_grpc.TrainingControlStub(channel)

@app.post("/rpc")
async def rpc_bridge(cmd: dict):
  t = cmd.get("type")
  try:
    if t == "pause":
      stub.Pause(training_pb2.Empty())
      return JSONResponse({"ok": True})
    if t == "resume":
      stub.Resume(training_pb2.Empty())
      return JSONResponse({"ok": True})
    if t == "delay":
      ms = int(cmd.get("ms", 0))
      stub.SetDelay(training_pb2.Delay(ms=ms))
      return JSONResponse({"ok": True})
    return JSONResponse({"ok": False, "error": "unknown command"}, status_code=400)
  except grpc.RpcError as e:
    return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

if __name__ == "__main__":
  uvicorn.run(app, host="0.0.0.0", port=8000)
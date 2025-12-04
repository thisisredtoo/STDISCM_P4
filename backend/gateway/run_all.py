# backend/gateway/run_all.py
import asyncio
import grpc
import uvicorn

from .ws_gateway import app as ws_app

from backend.grpc_stubs import dashboard_pb2, dashboard_pb2_grpc
from backend.grpc_stubs import training_pb2, training_pb2_grpc
from backend.services.dashboard_server import DashboardServicer
from backend.services.training_server import TrainingServicer 

async def serve_grpc(port: int = 50051):
    server = grpc.aio.server()
    dashboard_pb2_grpc.add_DashboardServicer_to_server(DashboardServicer(), server)
    try:
        training_pb2_grpc.add_TrainingServicer_to_server(TrainingServicer(), server)
    except Exception:
        pass
    server.add_insecure_port(f"[::]:{port}")
    await server.start()
    await server.wait_for_termination()

async def serve_ws(host: str = "0.0.0.0", port: int = 8000):
    config = uvicorn.Config(ws_app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    await asyncio.gather(serve_grpc(), serve_ws())

if __name__ == "__main__":
    asyncio.run(main())
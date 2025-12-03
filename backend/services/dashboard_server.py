#!/usr/bin/env python3
"""
ML Training Dashboard Server (Headless gRPC → WS bridge)
- Implements Dashboard gRPC service using grpc.aio
- Forwards updates to the FastAPI WebSocket gateway (publisher/broadcaster)
- No GUI / Tk dependencies
"""

import asyncio
import base64
import grpc

from backend.grpc_stubs import dashboard_pb2, dashboard_pb2_grpc
from backend.gateway.publisher import broadcaster


class DashboardServicer(dashboard_pb2_grpc.DashboardServicer):
    """
    Receives training updates via gRPC and relays them to the WebSocket broadcaster.
    """

    async def SendBatchUpdate(self, request: dashboard_pb2.BatchUpdate, context):
        # Convert raw bytes → data URLs for the browser
        images = [
            "data:image/jpeg;base64," + base64.b64encode(img.image).decode()
            for img in request.images
        ]
        payload = {
            "type": "batch",
            "index": int(request.index),
            "images": images[:16],                       # enforce 16 tiles
            "y_pred": list(request.predictions)[:16],
            "y_true": list(request.groundTruths)[:16],
        }
        await broadcaster.publish_json(payload)
        return dashboard_pb2.UpdateReply(status=True, message="ok", errorCode=0)

    async def SendLossUpdate(self, request: dashboard_pb2.LossUpdate, context):
        payload = {
            "type": "loss",
            "iteration": int(request.iteration),
            "loss": float(request.lossValue),
        }
        await broadcaster.publish_json(payload)
        return dashboard_pb2.UpdateReply(status=True, message="ok", errorCode=0)


async def serve(port: int = 50051) -> None:
    """
    Start the async gRPC server for the Dashboard service.
    Run your WS gateway separately (or with run_all.py).
    """
    server = grpc.aio.server(options=[
        ('grpc.max_send_message_length', 50 * 1024 * 1024),
        ('grpc.max_receive_message_length', 50 * 1024 * 1024),
    ])
    dashboard_pb2_grpc.add_DashboardServicer_to_server(DashboardServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    await server.start()
    print(f"✓ Dashboard gRPC listening on :{port}")
    try:
        await server.wait_for_termination()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        await server.stop(0)


def main():
    asyncio.run(serve())


if __name__ == "__main__":
    main()
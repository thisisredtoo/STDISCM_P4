# backend/services/training_server.py
import asyncio
import grpc

from backend.grpc_stubs import training_pb2, training_pb2_grpc
from backend.gateway.publisher import broadcaster

class TrainingServicer(training_pb2_grpc.TrainingServicer):
    async def TrainingStatusUpdate(self, request: training_pb2.TrainingStatus, context):
        await broadcaster.publish_json({
            "type": "status",
            "isTraining": bool(request.isTraining),
            "statusMessage": request.statusMessage,
        })
        return training_pb2.UpdateReply(status=True, message="ok", errorCode=0)

    async def TrainingMetricsUpdate(self, request: training_pb2.TrainingMetrics, context):
        await broadcaster.publish_json({
            "type": "metrics",
            "iteration": int(request.currentIteration),
            "loss": float(request.currentLoss),
        })
        return training_pb2.UpdateReply(status=True, message="ok", errorCode=0)

async def _serve_training_only(port: int = 50052):
    server = grpc.aio.server()
    training_pb2_grpc.add_TrainingServicer_to_server(TrainingServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    await server.start()
    await server.wait_for_termination()

if __name__ == "__main__":
    asyncio.run(_serve_training_only())
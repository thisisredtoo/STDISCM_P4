import asyncio
import base64
import grpc

from backend.grpc_stubs import dashboard_pb2, dashboard_pb2_grpc
from backend.gateway.publisher import broadcaster

class DashboardServicer(dashboard_pb2_grpc.DashboardServicer):
    async def SendBatchUpdate(self, request, context):
        try:
            images = [
                "data:image/jpeg;base64," + base64.b64encode(img.image).decode()
                for img in request.images
            ][:16]

            labels = list(request.groundTruths)[:16]
            preds = list(request.predictions)[:16]

            await broadcaster.publish_json({"type": "images", "payload": images})
            await broadcaster.publish_json({"type": "labels", "payload": labels})
            await broadcaster.publish_json({"type": "preds", "payload": preds})

            print(f"[WS OK] batch idx={int(request.index)}")
            return dashboard_pb2.UpdateReply(status=True, message="ok", errorCode=0)

        except Exception as e:
            print(f"[WS ERROR] batch: {e}")
            return dashboard_pb2.UpdateReply(status=False, message=str(e), errorCode=1)


    async def SendLossUpdate(self, request, context):
        try:
            pair = [int(request.iteration), float(request.lossValue)]
            await broadcaster.publish_json({"type": "loss", "payload": pair})

            print(f"[WS OK] loss iter={pair[0]} val={pair[1]:.6f}")
            return dashboard_pb2.UpdateReply(status=True, message="ok", errorCode=0)

        except Exception as e:
            print(f"[WS ERROR] loss: {e}")
            return dashboard_pb2.UpdateReply(status=False, message=str(e), errorCode=1)


async def serve(port: int = 50051):
    server = grpc.aio.server()
    dashboard_pb2_grpc.add_DashboardServicer_to_server(DashboardServicer(), server)
    server.add_insecure_port(f"[::]:{port}")

    await server.start()
    print(f"✓ Dashboard gRPC listening on :{port}")
    await server.wait_for_termination()

def main():
    asyncio.run(serve())


if __name__ == "__main__":
    main()


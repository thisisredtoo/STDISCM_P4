import grpc
from concurrent import futures
import time

import dashboard_pb2
import dashboard_pb2_grpc

# Shared global variables
latest_batch = None
latest_loss = None

class DashboardService(dashboard_pb2_grpc.DashboardServicer):

    # Receive images + predictions + ground truths
    def SendBatchUpdate(self, request, context):
        global latest_batch
        latest_batch = request

        # Print summary in terminal -> replace with updating to UI
        print(f"\n[SERVER] Received batch index {request.index} | {len(request.images)} images")
        for i in range(len(request.images)):
            pred = request.predictions[i] if i < len(request.predictions) else "N/A"
            gt = request.groundTruths[i] if i < len(request.groundTruths) else "N/A"
            correct = "✓" if pred == gt else "✗"
            print(f"  Image {i}: GT = {gt}, Pred = {pred} {correct}")

        return dashboard_pb2.UpdateReply(status=True, message="Batch received")

    # Receive loss updates
    def SendLossUpdate(self, request, context):
        global latest_loss
        latest_loss = request
        print(f"[SERVER] Received loss: {request.lossValue:.5f} at iteration {request.iteration}")
        return dashboard_pb2.UpdateReply(status=True, message="Loss received")

def serve():
    print("[SERVER] Starting gRPC Dashboard server on port 50051...")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
    dashboard_pb2_grpc.add_DashboardServicer_to_server(DashboardService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("[SERVER] Ready to accept connections.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop(0)
        print("[SERVER] Stopped.")

if __name__ == "__main__":
    serve()


# --------------------------- WITH TRAINING.PROTO ---------------------------
# import grpc
# from concurrent import futures
# import time

# import dashboard_pb2
# import dashboard_pb2_grpc
# import training_pb2
# import training_pb2_grpc

# # Shared state
# latest_batch = None
# latest_loss = None
# training_status = None
# training_metrics = None

# # --- Dashboard Service ---
# class DashboardService(dashboard_pb2_grpc.DashboardServicer):
#     def SendBatchUpdate(self, request, context):
#         global latest_batch
#         latest_batch = request
#         print(f"[DASHBOARD] Received batch {request.index}")
#         return dashboard_pb2.UpdateReply(status=True, message="Batch received", errorCode=0)

#     def SendLossUpdate(self, request, context):
#         global latest_loss
#         latest_loss = request
#         print(f"[DASHBOARD] Received loss {request.lossValue} at iteration {request.iteration}")
#         return dashboard_pb2.UpdateReply(status=True, message="Loss received", errorCode=0)

# # --- Training Service ---
# class TrainingService(training_pb2_grpc.TrainingServicer):
#     def TrainingStatusUpdate(self, request, context):
#         global training_status
#         training_status = request
#         print(f"[TRAINING] Status: {request.statusMessage}, isTraining={request.isTraining}")
#         return training_pb2.UpdateReply(status=True, message="Status received", errorCode=0)

#     def TrainingMetricsUpdate(self, request, context):
#         global training_metrics
#         training_metrics = request
#         print(f"[TRAINING] Iteration {request.currentIteration}, Loss {request.currentLoss}")
#         return training_pb2.UpdateReply(status=True, message="Metrics received", errorCode=0)

# # --- Server Startup ---
# def serve():
#     server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
#     dashboard_pb2_grpc.add_DashboardServicer_to_server(DashboardService(), server)
#     training_pb2_grpc.add_TrainingServicer_to_server(TrainingService(), server)

#     server.add_insecure_port('[::]:50051')
#     print("[SERVER] gRPC server running on port 50051...")
#     server.start()
#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         server.stop(0)
#         print("[SERVER] Server stopped.")

# if __name__ == "__main__":
#     serve()

import time
import threading
import grpc
from concurrent import futures
from backend.grpc_stubs import training_pb2, training_pb2_grpc

_pause = threading.Event()
_pause.set()  # start as running
_delay_ms = 0

class TrainingControl(training_pb2_grpc.TrainingControlServicer):
  def Pause(self, request, context):
    _pause.clear()
    return training_pb2.Empty()
  def Resume(self, request, context):
    _pause.set()
    return training_pb2.Empty()
  def SetDelay(self, request, context):
    global _delay_ms
    _delay_ms = max(0, int(request.ms))
    return training_pb2.Empty()

# Call these from your training loop

def wait_if_paused():
  while not _pause.is_set():
    time.sleep(0.05)

def maybe_delay():
  if _delay_ms:
    time.sleep(_delay_ms / 1000.0)

# gRPC server bootstrap

def serve():
  server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
  training_pb2_grpc.add_TrainingControlServicer_to_server(TrainingControl(), server)
  server.add_insecure_port("[::]:50051")
  server.start()
  server.wait_for_termination()

if __name__ == "__main__":
  serve()
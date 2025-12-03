# --------------------------- WITH TRAINING.PROTO ---------------------------

import grpc
import pickle
import numpy as np
import time
import os

from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import cross_val_score
from sklearn.metrics import classification_report

from backend.grpc_stubs import dashboard_pb2
from backend.grpc_stubs import dashboard_pb2_grpc
from backend.grpc_stubs import training_pb2
from backend.grpc_stubs import training_pb2_grpc

# ----------------------------
# gRPC client setup
# ----------------------------
channel = grpc.insecure_channel('localhost:50051')
dashboard_stub = dashboard_pb2_grpc.DashboardStub(channel)
training_stub = training_pb2_grpc.TrainingStub(channel)

def send_dashboard_batch(batch_index, predictions, ground_truths):
    """Send batch predictions + ground truths to Dashboard."""
    batch_msg = dashboard_pb2.BatchUpdate(
        index=batch_index,
        images=[dashboard_pb2.ImageData(image=b'')] * len(predictions),  # placeholder for images
        predictions=[str(p) for p in predictions],
        groundTruths=[str(gt) for gt in ground_truths]
    )
    try:
        dashboard_stub.SendBatchUpdate(batch_msg)
    except grpc.RpcError as e:
        print("[CLIENT] Failed to send dashboard batch:", e)

def send_dashboard_loss(iteration, loss_value):
    """Send batch loss to Dashboard."""
    loss_msg = dashboard_pb2.LossUpdate(
        iteration=iteration,
        lossValue=float(loss_value)
    )
    try:
        dashboard_stub.SendLossUpdate(loss_msg)
    except grpc.RpcError as e:
        print("[CLIENT] Failed to send dashboard loss:", e)

def send_training_status(is_training, message):
    """Send training status update."""
    status_msg = training_pb2.TrainingStatus(
        isTraining=is_training,
        statusMessage=message
    )
    try:
        training_stub.TrainingStatusUpdate(status_msg)
    except grpc.RpcError as e:
        print("[CLIENT] Failed to send training status:", e)

def send_training_metrics(iteration, loss):
    """Send training metrics update."""
    metrics_msg = training_pb2.TrainingMetrics(
        currentIteration=float(iteration),
        currentLoss=float(loss)
    )
    try:
        training_stub.TrainingMetricsUpdate(metrics_msg)
    except grpc.RpcError as e:
        print("[CLIENT] Failed to send training metrics:", e)

# ----------------------------
# Load CIFAR-10 data
# ----------------------------
def load_CIFAR_batch(filename):
    with open(filename, 'rb') as f:
        datadict = pickle.load(f, encoding='latin1')
        X = datadict['data']
        Y = datadict['labels']
        X = X.reshape(10000, 3, 32, 32).transpose(0, 2, 3, 1).astype("float")
        Y = np.array(Y)
    return X, Y

def load_CIFAR10(ROOT):
    xs, ys = [], []
    for b in range(1, 6):
        f = os.path.join(ROOT, 'data_batch_%d' % b)
        X, Y = load_CIFAR_batch(f)
        xs.append(X)
        ys.append(Y)
    X_train = np.concatenate(xs)
    Y_train = np.concatenate(ys)
    X_test, Y_test = load_CIFAR_batch(os.path.join(ROOT, 'test_batch'))
    return X_train, Y_train, X_test, Y_test

cifar10_dir = r'C:\Users\Erika Alvarez\OneDrive\Desktop\P4_STDISCM\cifar-10-python\cifar-10-batches-py'
X_train, y_train, X_test, y_test = load_CIFAR10(cifar10_dir)

# Subsample for faster testing
num_training = 5000
num_test = 500
X_train = X_train[:num_training]
y_train = y_train[:num_training]
X_test = X_test[:num_test]
y_test = y_test[:num_test]

classes = ['plane', 'car', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck']

# Flatten images for kNN
X_train_flat = X_train.reshape(X_train.shape[0], -1)
X_test_flat = X_test.reshape(X_test.shape[0], -1)

# ----------------------------
# Send initial training status
# ----------------------------
send_training_status(True, "Starting kNN training")

# ----------------------------
# Train kNN model
# ----------------------------
k = 5
model = KNeighborsClassifier(n_neighbors=k)
model.fit(X_train_flat, y_train)

# ----------------------------
# Simulate batch evaluation
# ----------------------------
batch_size = 16
num_batches = len(X_test_flat) // batch_size

for batch_idx in range(num_batches):
    start = batch_idx * batch_size
    end = start + batch_size
    X_batch = X_test_flat[start:end]
    y_batch = y_test[start:end]

    y_pred = model.predict(X_batch)

    # Simulate a "loss" metric: 1 - accuracy
    batch_accuracy = np.mean(y_pred == y_batch)
    batch_loss = 1 - batch_accuracy

    # Send batch to Dashboard
    send_dashboard_batch(
        batch_index=batch_idx,
        predictions=[classes[p] for p in y_pred],
        ground_truths=[classes[gt] for gt in y_batch]
    )

    # Send batch loss to Dashboard
    send_dashboard_loss(batch_idx, batch_loss)

    # Send overall training metrics
    send_training_metrics(batch_idx, batch_loss)

    print(f"[CLIENT] Sent batch {batch_idx}, batch loss: {batch_loss:.4f}")

    time.sleep(0.5)  # short delay to simulate real-time training

# ----------------------------
# Send final training status
# ----------------------------
send_training_status(False, "kNN training completed")
print("[CLIENT] Done sending all batches and training updates.")

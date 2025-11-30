# -*- coding: utf-8 -*-
import os
import random
import time
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.model_selection import train_test_split

# --- gRPC imports ---
import grpc
import dashboard_pb2
import dashboard_pb2_grpc

# ---------------------------
#  CONFIGURATION
# ---------------------------
DATA_DIR = "./vehicle_classification/Vehicles/"
IMG_SIZE = (224, 224)
BATCH_SIZE = 16
EPOCHS = 5

# ---------------------------
#  DOWNLOAD DATASET IF NEEDED
# ---------------------------
import requests, zipfile, io

if not os.path.exists(DATA_DIR):
    print("Downloading dataset...")
    url = "https://www.kaggle.com/api/v1/datasets/download/mohamedmaher5/vehicle-classification"
    response = requests.get(url)
    z = zipfile.ZipFile(io.BytesIO(response.content))
    z.extractall("vehicle_classification")
    print("Dataset downloaded and extracted.")

# ---------------------------
#  LOAD CLASSES & PATHS
# ---------------------------
classes = sorted([d.name for d in os.scandir(DATA_DIR) if d.is_dir()])
print("Classes:", classes)

image_paths = []
image_labels = []

for idx, cls in enumerate(classes):
    cls_dir = os.path.join(DATA_DIR, cls)
    for fname in os.listdir(cls_dir):
        if fname.lower().endswith((".jpg", ".jpeg", ".png")):
            image_paths.append(os.path.join(cls_dir, fname))
            image_labels.append(idx)

print("Total images:", len(image_paths))

# Split train / validation
train_paths, val_paths, train_labels, val_labels = train_test_split(
    image_paths, image_labels, test_size=0.2, stratify=image_labels, random_state=42
)
print("Train images:", len(train_paths), "Validation images:", len(val_paths))

# ---------------------------
#  DATA LOADING + PREPROCESSING
# ---------------------------
def load_and_preprocess(path):
    img = Image.open(path).convert("RGB")
    img = img.resize(IMG_SIZE)
    arr = np.array(img) / 255.0
    return arr

def data_generator(paths, labels, batch_size, shuffle=True):
    idxs = list(range(len(paths)))
    while True:
        if shuffle:
            random.shuffle(idxs)
        for start in range(0, len(paths), batch_size):
            batch_idx = idxs[start:start+batch_size]
            batch_images = []
            batch_labels = []
            for i in batch_idx:
                batch_images.append(load_and_preprocess(paths[i]))
                batch_labels.append(labels[i])
            yield np.stack(batch_images, axis=0), np.array(batch_labels)

# ---------------------------
#  BUILD MODEL
# ---------------------------
num_classes = len(classes)

base_model = keras.applications.MobileNetV2(
    input_shape=(IMG_SIZE[0], IMG_SIZE[1], 3),
    include_top=False,
    weights="imagenet"
)
base_model.trainable = False

model = keras.Sequential([
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dense(128, activation="relu"),
    layers.Dropout(0.5),
    layers.Dense(num_classes, activation="softmax")
])

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=1e-4),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

model.summary()

# ---------------------------
#  gRPC CLIENT SETUP
# ---------------------------
channel = grpc.insecure_channel("localhost:50051")
stub = dashboard_pb2_grpc.DashboardStub(channel)

def send_loss_update(loss_value, iteration):
    try:
        stub.SendLossUpdate(dashboard_pb2.LossUpdate(
            lossValue=float(loss_value),
            iteration=iteration
        ))
    except grpc.RpcError as e:
        print("gRPC LossUpdate error:", e)

def send_batch_update(images, predictions, ground_truths, index=0):
    try:
        image_msgs = [dashboard_pb2.ImageData(image=(img*255).astype(np.uint8).tobytes()) for img in images]
        stub.SendBatchUpdate(dashboard_pb2.BatchUpdate(
            index=index,
            images=image_msgs,
            predictions=predictions,
            groundTruths=ground_truths
        ))
    except grpc.RpcError as e:
        print("gRPC BatchUpdate error:", e)

# ---------------------------
#  CUSTOM TRAINING LOOP
# ---------------------------
train_gen = data_generator(train_paths, train_labels, BATCH_SIZE, shuffle=True)
val_gen = data_generator(val_paths, val_labels, BATCH_SIZE, shuffle=False)

steps_per_epoch = len(train_paths) // BATCH_SIZE
val_steps = len(val_paths) // BATCH_SIZE

iteration = 0
for epoch in range(EPOCHS):
    print(f"Epoch {epoch+1}/{EPOCHS}")
    for step in range(steps_per_epoch):
        X_batch, y_batch = next(train_gen)
        
        # Train on batch
        metrics = model.train_on_batch(X_batch, y_batch)
        loss_value = metrics[0]
        acc_value = metrics[1]
        
        # Send updates to dashboard
        send_loss_update(loss_value, iteration)
        preds = model.predict(X_batch, verbose=0)
        pred_classes = [classes[np.argmax(p)] for p in preds]
        gt_classes = [classes[y] for y in y_batch]
        send_batch_update(X_batch, pred_classes, gt_classes, index=iteration)
        
        if step % 10 == 0:
            print(f"Step {step}, Loss: {loss_value:.4f}, Acc: {acc_value:.4f}")
        
        iteration += 1

# ---------------------------
#  OPTIONAL: Plot validation metrics
# ---------------------------
val_metrics = []
for step in range(val_steps):
    X_val, y_val = next(val_gen)
    metrics = model.test_on_batch(X_val, y_val)
    val_metrics.append(metrics)

val_loss = np.mean([m[0] for m in val_metrics])
val_acc = np.mean([m[1] for m in val_metrics])
print(f"Validation - Loss: {val_loss:.4f}, Acc: {val_acc:.4f}")

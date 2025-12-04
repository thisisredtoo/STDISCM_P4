import os, time, numpy as np, torch, torch.nn as nn, torch.optim as optim
import torchvision
import torchvision.transforms as T
import grpc

from backend.grpc_stubs import dashboard_pb2, dashboard_pb2_grpc, training_pb2, training_pb2_grpc
from backend.clients._helpers import select_16, make_image_msgs, to_names

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
BATCH = 128                 # training batch size
DISPLAY_TILE_COUNT = 16     # per spec
LOSS_THROTTLE = 2           # send loss every N=2 batches (fits N…N×10)

# ---- gRPC (sync client is fine)
channel = grpc.insecure_channel("localhost:50051")
dash = dashboard_pb2_grpc.DashboardStub(channel)
train = training_pb2_grpc.TrainingStub(channel)

def send_status(is_training: bool, msg: str):
    try:
        train.TrainingStatusUpdate(training_pb2.TrainingStatus(isTraining=is_training, statusMessage=msg))
    except grpc.RpcError: pass

def send_metrics(iteration: int, loss: float):
    try:
        train.TrainingMetricsUpdate(training_pb2.TrainingMetrics(currentIteration=float(iteration),
                                                                 currentLoss=float(loss)))
    except grpc.RpcError: pass

def send_batch(idx: int, images_hwc_uint8, y_true_idx, y_pred_idx):
    try:
        imgs = make_image_msgs(images_hwc_uint8)
        dash.SendBatchUpdate(dashboard_pb2.BatchUpdate(
            index=idx,
            images=imgs,
            predictions=to_names(y_pred_idx),
            groundTruths=to_names(y_true_idx),
        ))
    except grpc.RpcError: pass

def send_loss(iteration: int, loss: float):
    try:
        dash.SendLossUpdate(dashboard_pb2.LossUpdate(iteration=iteration, lossValue=float(loss)))
    except grpc.RpcError: pass

# ---- Simple model
class SmallCNN(nn.Module):
    def __init__(self, n=10):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(3,32,3,padding=1), nn.ReLU(),
            nn.Conv2d(32,32,3,padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32,64,3,padding=1), nn.ReLU(),
            nn.Conv2d(64,64,3,padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Flatten(), nn.Linear(64*8*8,256), nn.ReLU(), nn.Linear(256,n)
        )
    def forward(self, x): return self.net(x)

def main():
    # Data
    tfm_train = T.Compose([
        T.RandomHorizontalFlip(), T.ToTensor(),
        T.Normalize((0.4914,0.4822,0.4465),(0.2023,0.1994,0.2010))
    ])
    tfm_vis = T.Compose([T.ToTensor()])   # for visuals only (no norm)
    trainset = torchvision.datasets.CIFAR10(root=os.path.expanduser("~/.data"), train=True, download=True, transform=tfm_train)
    visset   = torchvision.datasets.CIFAR10(root=os.path.expanduser("~/.data"), train=True, download=True, transform=None)  # raw PIL
    loader   = torch.utils.data.DataLoader(trainset, batch_size=BATCH, shuffle=True, num_workers=2, drop_last=True)

    model = SmallCNN().to(DEVICE)
    opt   = optim.AdamW(model.parameters(), lr=1e-3)
    crit  = nn.CrossEntropyLoss()

    send_status(True, "Training started")
    it = 0
    for epoch in range(1):           # extend epochs as needed
        for xb, yb in loader:
            it += 1
            xb, yb = xb.to(DEVICE), yb.to(DEVICE)
            model.train()
            opt.zero_grad()
            logits = model(xb)
            loss = crit(logits, yb)
            loss.backward()
            opt.step()

            # Predictions & visuals for the dashboard
            with torch.no_grad():
                preds = logits.argmax(1).cpu().numpy()
                y_np  = yb.cpu().numpy()

            # get the raw HWC uint8 images for exactly 16 tiles
            # we fetch the same indices from the untransformed visset (cost: small)
            # choose the first indices of this batch in the epoch order
            # loader doesn't expose raw indices, so we just build a quick proxy:
            # Take first DISPLAY_TILE_COUNT samples from the *next* raw batch for visuals
            # Simpler: convert back to [0..255] from normalized xb (approx)
            imgs = (xb[:DISPLAY_TILE_COUNT].detach().cpu().numpy().transpose(0,2,3,1))
            imgs = (np.clip(((imgs * np.array([0.2023,0.1994,0.2010])) + np.array([0.4914,0.4822,0.4465]))*255, 0, 255)).astype(np.uint8)

            sel_imgs, sel_true, sel_pred = select_16(imgs, y_np[:DISPLAY_TILE_COUNT], preds[:DISPLAY_TILE_COUNT])
            send_batch(it, sel_imgs, sel_true, sel_pred)

            if it % LOSS_THROTTLE == 0:
                send_loss(it, float(loss.item()))
                send_metrics(it, float(loss.item()))

    send_status(False, "Training finished")
    print("Done")

if __name__ == "__main__":
    main()

# # backend/clients/train_demo.py
# import asyncio
# import numpy as np
# import requests
# from backend.clients._helpers import to_names, make_image_msgs, serialize_image_msgs

# DISPLAY_TILE_COUNT = 16  # exactly 16 tiles per spec
# BATCH_INTERVAL = 0.2     # seconds between fake batches
# TOTAL_BATCHES = 50       # how many fake batches to send
# LOSS_START = 1.0
# LOSS_DECAY = 0.95        # exponential decay per batch

# WS_PUBLISH_URL = "http://localhost:8000/publish"

# def send_batch_ws(idx, images, y_true_idx, y_pred_idx):
#     payload = {
#         "type": "batch",
#         "index": idx,
#         "images": serialize_image_msgs(make_image_msgs(images)),
#         "predictions": to_names(y_pred_idx),
#         "groundTruths": to_names(y_true_idx),
#     }
#     try:
#         requests.post(WS_PUBLISH_URL, json=payload)
#     except Exception as e:
#         print("Failed to send batch:", e)

# def send_loss_ws(iteration, loss):
#     payload = {"type": "loss", "iteration": iteration, "lossValue": loss}
#     try:
#         requests.post(WS_PUBLISH_URL, json=payload)
#     except Exception as e:
#         print("Failed to send loss:", e)

# def generate_fake_batch():
#     # generate random images (HWC uint8) and labels
#     images = (np.random.rand(DISPLAY_TILE_COUNT, 32, 32, 3) * 255).astype(np.uint8)
#     labels = np.random.randint(0, 10, size=(DISPLAY_TILE_COUNT,))
#     preds  = np.random.randint(0, 10, size=(DISPLAY_TILE_COUNT,))
#     return images, labels, preds

# async def main():
#     print("Demo training started...")
#     loss = LOSS_START
#     for i in range(1, TOTAL_BATCHES + 1):
#         images, y_true, y_pred = generate_fake_batch()
#         send_batch_ws(i, images, y_true, y_pred)
#         send_loss_ws(i, loss)
#         print(f"Sent batch {i}, loss {loss:.4f}")
#         loss *= LOSS_DECAY
#         await asyncio.sleep(BATCH_INTERVAL)
#     # final status
#     payload = {"type": "status", "isTraining": False, "statusMessage": "Demo finished"}
#     try:
#         requests.post(WS_PUBLISH_URL, json=payload)
#     except:
#         pass
#     print("Demo training finished.")

# if __name__ == "__main__":
#     asyncio.run(main())


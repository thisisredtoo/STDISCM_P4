import os, time, numpy as np, torch, torch.nn as nn, torch.optim as optim
import torchvision
import torchvision.transforms as T
import grpc

from backend.grpc_stubs import dashboard_pb2, dashboard_pb2_grpc, training_pb2, training_pb2_grpc
from backend.clients._helpers import select_16, make_image_msgs, to_names

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
BATCH = 128                
DISPLAY_TILE_COUNT = 16     
LOSS_THROTTLE = 2        

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
    for epoch in range(1):          
        for xb, yb in loader:
            it += 1
            xb, yb = xb.to(DEVICE), yb.to(DEVICE)
            model.train()
            opt.zero_grad()
            logits = model(xb)
            loss = crit(logits, yb)
            loss.backward()
            opt.step()

            with torch.no_grad():
                preds = logits.argmax(1).cpu().numpy()
                y_np  = yb.cpu().numpy()

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

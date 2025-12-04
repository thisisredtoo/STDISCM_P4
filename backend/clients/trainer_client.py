# backend/clients/trainer_client.py
import asyncio
import io
from typing import List

import grpc
from PIL import Image 

from backend.grpc_stubs import dashboard_pb2, dashboard_pb2_grpc


def make_dummy_jpeg(w: int = 256, h: int = 256, color=(60, 120, 200)) -> bytes:
    img = Image.new("RGB", (w, h), color)
    for x in range(w):
        img.putpixel((x, x % h), (color[0], (color[1] + x) % 255, (color[2] + 2 * x) % 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


async def send_batch_and_loss(
    channel: grpc.aio.Channel,
    imgs_bytes: List[bytes],
    preds: List[str],
    truths: List[str],
    idx: int,
    loss: float,
    it: int,
):
    stub = dashboard_pb2_grpc.DashboardStub(channel)

    await stub.SendBatchUpdate(
        dashboard_pb2.BatchUpdate(
            images=[dashboard_pb2.ImageData(image=b) for b in imgs_bytes],
            predictions=preds,
            groundTruths=truths,
            index=idx,
        )
    )

    await stub.SendLossUpdate(
        dashboard_pb2.LossUpdate(lossValue=float(loss), iteration=int(it))
    )


async def demo():
    async with grpc.aio.insecure_channel("localhost:50051") as ch:
        imgs = [make_dummy_jpeg(color=(60 + 10 * i, 120, 200)) for i in range(16)]
        preds = [str(i % 10) for i in range(16)]
        truths = [str((i + 1) % 10) for i in range(16)]

        for it in range(1, 6):
            loss = 1.0 / it
            await send_batch_and_loss(ch, imgs, preds, truths, idx=it, loss=loss, it=it)
            await asyncio.sleep(0.3)


if __name__ == "__main__":
    asyncio.run(demo())
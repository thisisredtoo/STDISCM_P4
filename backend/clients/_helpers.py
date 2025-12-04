import io, random
from typing import List, Tuple
import numpy as np
from PIL import Image
from backend.grpc_stubs import dashboard_pb2

CLASSES = ['plane','car','bird','cat','deer','dog','frog','horse','ship','truck']

def select_16(images_hwc: np.ndarray, y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    n = len(images_hwc)
    if n >= 16:
        idx = sorted(random.sample(range(n), 16))
        return images_hwc[idx], y_true[idx], y_pred[idx]
    reps = (16 + n - 1) // n
    img = np.concatenate([images_hwc]*reps, axis=0)[:16]
    yt  = np.concatenate([y_true]*reps, axis=0)[:16]
    yp  = np.concatenate([y_pred]*reps, axis=0)[:16]
    return img, yt, yp

def to_jpeg_bytes(img_hwc: np.ndarray, max_side=256, quality=85) -> bytes:
    pil = Image.fromarray(img_hwc.astype(np.uint8))
    if max(pil.size) > max_side:
        pil.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    pil.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()

def make_image_msgs(images_hwc: np.ndarray) -> List[dashboard_pb2.ImageData]:
    return [dashboard_pb2.ImageData(image=to_jpeg_bytes(im), width=im.shape[1], height=im.shape[0])
            for im in images_hwc]

def to_names(y: np.ndarray) -> List[str]:
    return [CLASSES[int(v)] for v in y]
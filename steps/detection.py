"""
Step 1 & 2: Defect Detection + Classification using Roboflow
"""

import os
from inference_sdk import InferenceHTTPClient


def detect_defects(image_path):
    api_key = os.getenv("ROBOFLOW_API_KEY", "")

    client = InferenceHTTPClient(
        api_url="https://detect.roboflow.com",
        api_key=api_key,
    )

    result = client.infer(image_path, model_id="metal-surface-defect-detection/1")

    defects = []
    for pred in result.get("predictions", []):
        x = int(pred["x"] - pred["width"] / 2)
        y = int(pred["y"] - pred["height"] / 2)
        w = int(pred["width"])
        h = int(pred["height"])

        defects.append({
            "type": pred["class"],
            "bbox": [x, y, x + w, y + h],
            "confidence": round(pred["confidence"], 2),
            "width": w,
            "height": h,
        })

    return defects

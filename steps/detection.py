import os
from inference_sdk import InferenceHTTPClient

# Roboflow API settings
ROBOFLOW_URL = "https://serverless.roboflow.com"
WORKSPACE    = "thamizh-bag2k"
WORKFLOW     = "custom-workflow"


def detect_defects(image_path):
    """Send image to Roboflow API, return list of detected defects."""
    api_key = os.getenv("ROBOFLOW_API_KEY", "")

    client = InferenceHTTPClient(api_url=ROBOFLOW_URL, api_key=api_key)

    result = client.run_workflow(
        workspace_name=WORKSPACE,
        workflow_id=WORKFLOW,
        images={"image": image_path},
        use_cache=True,
    )

    # Parse the API response into a clean list
    predictions = _get_predictions(result)
    defects = []

    for p in predictions:
        # Roboflow gives center coords — convert to top-left corner
        w = int(p["width"])
        h = int(p["height"])
        x1 = int(p["x"] - w / 2)
        y1 = int(p["y"] - h / 2)

        defects.append({
            "type": p["class"],              # e.g. "Dented", "Scratch"
            "bbox": [x1, y1, x1 + w, y1 + h],  # [x1, y1, x2, y2]
            "confidence": round(p["confidence"], 2),
            "width": w,
            "height": h,
        })

    return defects


def _get_predictions(result):
    """Extract the predictions list from Roboflow's nested response."""
    if not result:
        return []

    entry = result[0] if isinstance(result, list) else result

    # Check common keys in the response
    for key in ("predictions", "model_predictions", "output"):
        val = entry.get(key)
        if val is None:
            continue
        if isinstance(val, dict) and "predictions" in val:
            return val["predictions"]
        if isinstance(val, list):
            return val

    # Fallback: search all values
    for val in entry.values():
        if isinstance(val, dict) and "predictions" in val:
            return val["predictions"]

    return []

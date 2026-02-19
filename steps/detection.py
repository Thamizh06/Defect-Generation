import os
from inference_sdk import InferenceHTTPClient

ROBOFLOW_URL = "https://serverless.roboflow.com"
WORKSPACE    = "thamizh-bag2k"
WORKFLOW     = "custom-workflow"

def detect_defects(image_path):
    api_key = os.getenv("ROBOFLOW_API_KEY", "")
    client  = InferenceHTTPClient(api_url=ROBOFLOW_URL, api_key=api_key)
    result  = client.run_workflow(
        workspace_name=WORKSPACE,
        workflow_id=WORKFLOW,
        images={"image": image_path},
        use_cache=True,
    )
    return result[0].get("predictions", []) if result else []

import json
import os
import base64
import boto3

# Use SageMaker Runtime Client (no SDK packaging needed)
sm_runtime = boto3.client("sagemaker-runtime")
ENDPOINT = "image-classification-2025-09-16-11-29-01-405"


def lambda_handler(event, context):
    """
    Decode base64 image from the previous step, invoke the SageMaker endpoint,
    and return 'inferences' (list of probabilities) in the body.
    """

    # Expect event body (if invoked directly by Step Functions with OutputPath=$.Payload.body)
    # If your state machine passes the raw Lambda #1 response, adjust to event["body"]["image_data"].
    image_b64 = event["image_data"]
    image_bytes = base64.b64decode(image_b64)

    # Invoke the endpoint (model expects PNG)
    response = sm_runtime.invoke_endpoint(
        EndpointName=ENDPOINT,
        ContentType="image/png",
        Body=image_bytes,
        Accept="application/json"
    )

    # Parse JSON array of probs, e.g. [0.91, 0.09]
    payload = response["Body"].read().decode("utf-8")
    try:
        inferences = json.loads(payload)
    except json.JSONDecodeError:
        # fallback for plain string like "[0.91, 0.09]"
        inferences = eval(payload)  # OK here because payload is from SM

    # Attach to event (preserve other fields for downstream steps)
    event["inferences"] = inferences

    return {
        "statusCode": 200,
        "body": event
    }
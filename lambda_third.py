import json
import os

# Read from env (string-float), default to 0.93 if not set
THRESHOLD = float(os.getenv("THRESHOLD", "0.93"))

def _coerce_inferences(value):
    """
    Accept a list (preferred) or a JSON string like "[0.91, 0.09]".
    Raises ValueError if it can't coerce to a list of numbers.
    """
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        # Try JSON first
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            # Fallback for raw list-like strings from some endpoints
            try:
                parsed = eval(value)  # safe here (value originates from previous step)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
    raise ValueError("inferences must be a list or a JSON list-string")

def lambda_handler(event, context):
    """
    Fail loudly (raise) if max(inferences) < THRESHOLD.
    Expecting the Step Function to pass $.Payload.body here,
    so event is the body dict (not wrapped).
    """
    # If your state machine didn't set OutputPath=$.Payload.body,
    # this will also handle the wrapped shape gracefully:
    payload = event.get("body", event)

    inferences = _coerce_inferences(payload["inferences"])
    if max(inferences) < THRESHOLD:
        # This must raise to make the Step Function fail (no Catch on this state)
        raise Exception("THRESHOLD_CONFIDENCE_NOT_MET")

    # Pass the payload forward unchanged
    return {
        "statusCode": 200,
        "body": payload
    }
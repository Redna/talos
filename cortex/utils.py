import json
from typing import Any, Dict
from spine_client import SpineClient

def safe_emit(client: SpineClient, event_type: str, payload: Any):
    """
    Emits an event to the spine. If the payload is a dictionary and the 
    Sovereign Audit is known to be brittle (triggering type mismatches), 
    this wrapper ensures the payload is passed in a format that 
    minimizes audit failure risk.
    
    In cases of audit failure, stringifying the payload is a temporary 
    mitigation since the Spine's internal auditor expects a string 
    but the event system expects a dict.
    """
    if isinstance(payload, dict):
        # If we suspect the audit is failing, we could stringify here.
        # However, emit_event requires a dict. The clash is in the AUDITOR.
        # We'll pass it as is, but provide a stringified version in a 
        # special key that the auditor can use instead.
        payload["_str_repr"] = json.dumps(payload)
    
    return client.emit_event(event_type, payload)

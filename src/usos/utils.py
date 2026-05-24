

def _error_payload(exc: Exception) -> dict:
    return {"error": str(exc)}
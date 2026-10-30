"""Small response-correlation policy for line-based chat.py subprocess."""
def response_action(question,answer,grounded=False):
    if not question:
        return "SUPPRESS_UNCORRELATED"
    if grounded:
        return "EVALUATE_EVIDENCE"
    return "ROUTE_NORMAL"

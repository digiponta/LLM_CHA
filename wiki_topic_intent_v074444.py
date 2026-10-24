"""Normalize explicit Japanese requests for a conversational topic."""
import re

TOPIC_REQUESTS={
    "/topic","話題を提供して","話題を教えて","何か話題はある",
    "何か話題はないか","何か話題ない","何か話題ある",
    "何か面白い話題は","話題を振って","話題を出して",
    "何か話そう","おすすめの話題は"
}
def is_topic_request(text):
    normalized=re.sub(r"[\s\u3000]+","",(text or "")).rstrip("？?！!。.")
    return normalized in TOPIC_REQUESTS

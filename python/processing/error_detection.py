def detect_errors(text):
    error_keywords = ["fatal", "error", "issue"]
    return sum(text.lower().count(keyword) for keyword in error_keywords)

import re

def normalize_log(content):
    lines = content.split("\n")
    normalized_lines = []

    for line in lines:
        # Lowercase
        line = line.lower()

        # Replace known patterns
        line = re.sub(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", "<ip>", line)  # IPs

        # Replace full Apache-style timestamps like [Sun Dec 04 04:47:44 2005]
        line = re.sub(r"\[\w{3} \w{3} \d{2} \d{2}:\d{2}:\d{2} \d{4}\]", "<timestamp>", line)

        # Also match SSH-style timestamps like "Dec 10 06:55:46"
        line = re.sub(r"\b[a-z]{3} \d{2} \d{2}:\d{2}:\d{2}", "<timestamp>", line)

        line = re.sub(r"\bport \d+", "port <port>", line)
        line = re.sub(r"child \d+", "child <id>", line)
        line = re.sub(r"\buser [a-z0-9_]+", "user <user>", line, flags=re.IGNORECASE)
        line = re.sub(r"/[^\s]*", "<path>", line)
        line = re.sub(r"\b\d+\b", "<id>", line)

        # Remove unwanted characters
        line = re.sub(r"[^\w<> ]+", "", line)

        # Normalize spaces
        line = re.sub(r"\s+", " ", line).strip()

        if line:
            normalized_lines.append(line)

    return "\n".join(normalized_lines)

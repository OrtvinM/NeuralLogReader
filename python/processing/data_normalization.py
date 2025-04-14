import re
import os
import contextlib
import io
from datetime import datetime

def clean_text(text):
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize

    nltk_resources = ['punkt', 'stopwords']
    nltk_data_path = os.path.expanduser("~/nltk_data")
    import nltk.data
    nltk.data.path.append(nltk_data_path)

    for resource in nltk_resources:
        try:
            nltk.data.find(f'tokenizers/{resource}')
        except LookupError:
            nltk.download(resource, download_dir=nltk_data_path, quiet=True)

    if not text or not isinstance(text, str):
        return "Error: Invalid text input."

    text = text.lower()
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    words = word_tokenize(text)
    words = [word for word in words if word not in stopwords.words('english')]

    return ' '.join(words)

def parse_log_line(line, log_type):
    if log_type == 'apache':
        pattern = re.compile(r"\[(?P<timestamp>.*?)\] \[(?P<level>\w+)\] ?(?:\[(?P<source>[^\]]+)\] )?(?P<message>.*)")
        match = pattern.match(line)
        if match:
            try:
                timestamp = datetime.strptime(match.group("timestamp"), "%a %b %d %H:%M:%S %Y")
            except ValueError:
                timestamp = None
            return {
                "timestamp": timestamp,
                "level": match.group("level").lower(),
                "source": match.group("source") or "apache",
                "message": clean_text(match.group("message")),
                "ip_address": None,
                "user": None,
            }

    elif log_type == 'openssh':
        pattern = re.compile(r"(?P<timestamp>\w{3} \d{1,2} \d{2}:\d{2}:\d{2}) [\w\-]+ (?P<source>\w+)\[\d+\]: (?P<message>.*)")
        match = pattern.match(line)
        if match:
            try:
                timestamp = datetime.strptime(match.group("timestamp") + " 2005", "%b %d %H:%M:%S %Y")
            except ValueError:
                timestamp = None
            message = match.group("message")
            ip_match = re.search(r"(\d{1,3}\.){3}\d{1,3}", message)
            user_match = re.search(r"user (\w+)", message)
            return {
                "timestamp": timestamp,
                "level": "info",
                "source": match.group("source"),
                "message": clean_text(message),
                "ip_address": ip_match.group(0) if ip_match else None,
                "user": user_match.group(1) if user_match else None,
            }
    return None

def normalize_log_file(filepath, log_type):
    normalized_data = []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
        for line in file:
            parsed = parse_log_line(line, log_type)
            if parsed:
                normalized_data.append(parsed)

    return normalized_data

# smart_detector.py
import tensorflow as tf
import pickle
import numpy as np
from tokenizer_pipeline import LogTokenizer
from normalise import normalize_log

# Paths
MODEL_PATH = "datasets/smart_detector_model.h5"
TOKENIZER_PATH = "datasets/tokenizer.pkl"

# Load tokenizer
def load_tokenizer(path=TOKENIZER_PATH):
    tokenizer = LogTokenizer()
    tokenizer.load(path)
    return tokenizer

# Load model
def load_model(path=MODEL_PATH):
    return tf.keras.models.load_model(path)

# Predict function
def predict_log(content, model, tokenizer):
    normalized = normalize_log(content)
    lines = normalized.splitlines()
    lines = [line for line in lines if line.strip()]
    if not lines:
        return None

    tokenizer.fit(lines)
    tokenized = tokenizer.transform(lines)

    prediction = model.predict(tokenized)
    avg_prediction = prediction.mean(axis=0)

    return avg_prediction 
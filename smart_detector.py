# smart_detector.py
import tensorflow as tf
import pickle
import numpy as np
from tokenizer_pipeline import LogTokenizer
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
def predict_log(log_text, model, tokenizer, max_length=20):
    lines = log_text.split("\n")
    sequences = tokenizer.transform(lines)
    predictions = model.predict(sequences, verbose=0)

    # average prediction over all lines
    avg_prediction = np.mean(predictions, axis=0)
    predicted_class = np.argmax(avg_prediction)
    confidence = np.max(avg_prediction)

    return predicted_class, confidence

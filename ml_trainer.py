import os
import json
import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MultiLabelBinarizer
from tokenizer_pipeline import LogTokenizer
import pickle

# === CONFIGURATION ===
DATASET_FOLDER = "datasets/training_data"
MODEL_OUTPUT_PATH = "datasets/smart_detector_model.h5"
TOKENIZER_OUTPUT_PATH = "datasets/smart_detector_tokenizer.pkl"
LABEL_ENCODER_OUTPUT_PATH = "datasets/label_encoder.pkl"

# === PARAMETERS ===
MAX_SEQUENCE_LENGTH = 100
EPOCHS = 30
BATCH_SIZE = 8

def load_data():
    X_texts = []
    y_labels = []

    print(f"Loading .json files from {DATASET_FOLDER}...")
    for filename in os.listdir(DATASET_FOLDER):
        if filename.endswith(".json"):
            full_path = os.path.join(DATASET_FOLDER, filename)
            with open(full_path, "r", encoding="utf-8") as f:
                sample = json.load(f)
            normalized_lines = sample.get("normalized", [])
            tags = sample.get("tags", [])
            if not normalized_lines or not tags:
                print(f"Skipping {filename} (missing normalized data or tags)")
                continue
            combined_text = " ".join(normalized_lines)
            X_texts.append(combined_text)
            y_labels.append(tags)

    print(f"Loaded {len(X_texts)} valid samples.")
    return X_texts, y_labels

def main():
    # 1. Load data
    X_texts, y_labels = load_data()

    if len(X_texts) < 5:
        print("Not enough training data! Add more logs to datasets/training_data/")
        return

    # 2. Tokenizer
    tokenizer = LogTokenizer(max_length=MAX_SEQUENCE_LENGTH)
    tokenizer.fit(X_texts)
    X_sequences = tokenizer.transform(X_texts)

    # 3. Encode labels
    mlb = MultiLabelBinarizer()
    y_encoded = mlb.fit_transform(y_labels)

    # 4. Train-validation split
    X_train, X_val, y_train, y_val = train_test_split(
        X_sequences, y_encoded, test_size=0.2, random_state=42
    )

    # 5. Build the model
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(MAX_SEQUENCE_LENGTH,)),
        tf.keras.layers.Embedding(input_dim=5000, output_dim=64),
        tf.keras.layers.GlobalAveragePooling1D(),
        tf.keras.layers.Dense(64, activation="relu"),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(y_encoded.shape[1], activation="sigmoid")  # multi-label
    ])

    model.compile(
        optimizer="adam",
        loss="binary_crossentropy",
        metrics=["accuracy"]
    )

    model.summary()

    # 6. Train the model
    model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE
    )

    # 7. Save model, tokenizer, and label encoder
    os.makedirs("datasets", exist_ok=True)

    model.save(MODEL_OUTPUT_PATH)
    tokenizer.save(TOKENIZER_OUTPUT_PATH)

    with open(LABEL_ENCODER_OUTPUT_PATH, "wb") as f:
        pickle.dump(mlb, f)

    print(f"Model saved to {MODEL_OUTPUT_PATH}")
    print(f"Tokenizer saved to {TOKENIZER_OUTPUT_PATH}")
    print(f"Label Encoder saved to {LABEL_ENCODER_OUTPUT_PATH}")

if __name__ == "__main__":
    main()

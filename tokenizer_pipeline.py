from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import pickle

class LogTokenizer:
    def __init__(self, num_words=10000, oov_token="<OOV>", max_length=20):
        self.tokenizer = Tokenizer(num_words=num_words, oov_token=oov_token)
        self.max_length = max_length
        self.fitted = False

    def fit(self, lines):
        self.tokenizer.fit_on_texts(lines)
        self.fitted = True

    def transform(self, lines):
        if not self.fitted:
            raise ValueError("Tokenizer not fitted yet. Call `fit()` first.")

        sequences = self.tokenizer.texts_to_sequences(lines)
        padded = pad_sequences(sequences, maxlen=self.max_length, padding='post', truncating='post')
        return padded

    def save(self, path="tokenizer.pkl"):
        with open(path, "wb") as f:
            pickle.dump(self.tokenizer, f)

    def load(self, path="tokenizer.pkl"):
        with open(path, "rb") as f:
            self.tokenizer = pickle.load(f)
        self.fitted = True

    def get_vocab(self):
        return self.tokenizer.word_index

from tokenizer_pipeline import LogTokenizer

# Sample normalized log lines (could come from your clean tab)
sample_logs = [
    "<timestamp> <error> mod_jk child <id> workerenv in error state <id>",
    "<timestamp> <notice> jk2_init found child <id> in scoreboard slot <id>",
    "<timestamp> <error> connection closed by <ip> port <port>"
]

# Create tokenizer and fit it
tokenizer = LogTokenizer(max_length=12)
tokenizer.fit(sample_logs)

# Transform logs into sequences
X = tokenizer.transform(sample_logs)

# Print the results
print("Tokenized Sequences:")
print(X)

print("\nVocabulary:")
print(tokenizer.get_vocab())

# Save tokenizer for later reuse
tokenizer.save("tokenizer.pkl")

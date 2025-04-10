import re
import nltk
import os
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Ensure correct NLTK resources are available
nltk_resources = ['punkt', 'stopwords']
nltk_data_path = os.path.expanduser("~/nltk_data")
nltk.data.path.append(nltk_data_path)  

for resource in nltk_resources:
    try:
        nltk.data.find(f'tokenizers/{resource}')
        print(f"[INFO] {resource} found!")
    except LookupError:
        print(f"[WARNING] {resource} NOT found! Downloading now...")
        nltk.download(resource, download_dir=nltk_data_path)

# Debug: Print where NLTK is looking for files
print("NLTK data search paths:", nltk.data.path)

def clean_text(text):
    """
    Preprocess the input text by:
    - Lowercasing
    - Removing punctuation
    - Removing stopwords
    - Tokenizing
    """
    if not text or not isinstance(text, str):
        print("Error: Received invalid text input")  
        return "Error: Invalid text input."

    print(f"Original Text: {text}")  
    text = text.lower()  # Convert to lowercase
    text = re.sub(r'\d+', '', text)  # Remove numbers
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    words = word_tokenize(text)  # Tokenization
    words = [word for word in words if word not in stopwords.words('english')]  # Remove stopwords

    cleaned_text = ' '.join(words)
    print(f"Cleaned Text: {cleaned_text}")  
    return cleaned_text

if __name__ == '__main__':
    sample_text = "ERROR: Failed to load module. WARNING: Memory usage is high."
    cleaned_text = clean_text(sample_text)
    print("Final Cleaned Text:", cleaned_text)

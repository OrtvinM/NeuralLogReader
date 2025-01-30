import argparse
import json
import os

def detect_errors(text):
    error_keywords = ["fatal", "error", "issue"]
    error_count = sum(text.lower().count(keyword) for keyword in error_keywords)
    return error_count

def process_text_input():
    text = input("Enter text: ")
    error_count = detect_errors(text)
    return {"message": "Text processed!", "errorCount": error_count}

def process_file_input(file_path):
    if not os.path.exists(file_path):
        return {"message": "File not found", "errorCount": 0}

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            error_count = detect_errors(content)
        return {"message": "File processed!", "errorCount": error_count}
    except Exception as e:
        return {"message": f"Error reading file: {str(e)}", "errorCount": 0}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Error Detection Script")
    parser.add_argument('--text', action='store_true', help="Flag to indicate text input processing")
    parser.add_argument('--file', type=str, help="File path for error detection")
    args = parser.parse_args()

    if args.text:
        text = input()
        result = {"message": "Text processed!", "errorCount": detect_errors(text)}
    elif args.file:
        result = process_file_input(args.file)
    else:
        result = {"message": "No input provided", "errorCount": 0}

    print(json.dumps(result))

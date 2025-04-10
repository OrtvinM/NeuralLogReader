import sys
import json
from processing.error_detection import process_text_input, process_file_input
from processing.data_normalization import clean_text

def main():
    """
    Handles incoming requests from Node.js and routes them to the appropriate function.
    """
    try:
        request_data = sys.stdin.read().strip()

        if not request_data:
            print(json.dumps({"message": "No input received", "errorCount": 0, "normalizedText": "Error: No input provided."}))
            return

        request_json = json.loads(request_data)
        result = {"message": "Invalid request format", "errorCount": 0, "normalizedText": "Error: No normalized text generated."}  # Default response

        if 'text' in request_json:
            raw_text = request_json['text']
            normalized_text = clean_text(raw_text)

            # Ensure we return a proper JSON response
            result = process_text_input(normalized_text)
            result["normalizedText"] = normalized_text

        elif 'file' in request_json:
            file_path = request_json['file']

            with open(file_path, 'r', encoding='utf-8') as file:
                raw_text = file.read()
                normalized_text = clean_text(raw_text)

            result = process_file_input(file_path)
            result["normalizedText"] = normalized_text  # Ensure normalized text is returned

        # Print ONLY the JSON response (no debug statements)
        print(json.dumps(result))

    except Exception as e:
        print(json.dumps({
            "message": f"Error processing request: {str(e)}",
            "errorCount": 0,
            "normalizedText": "Error: Exception occurred."
        }))

if __name__ == '__main__':
    main()

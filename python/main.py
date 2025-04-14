import sys
import os
import json
import tempfile
from processing.error_detection import detect_errors
from processing.data_normalization import normalize_log_file

def main():
    try:
        request_data = sys.stdin.read().strip()

        if not request_data:
            result = {
                "message": "No input received",
                "errorCount": 0,
                "normalizedText": "Error: No input provided."
            }
        else:
            request_json = json.loads(request_data)
            result = {
                "message": "Invalid request format",
                "errorCount": 0,
                "normalizedText": "Error: No normalized text generated."
            }

            if 'text' in request_json:
                raw_text = request_json['text']
                error_count = detect_errors(raw_text)
                result = {
                    "message": "Text processed!",
                    "errorCount": error_count,
                    "normalizedText": raw_text
                }

            elif 'file' in request_json and 'logType' in request_json:
                file_path = request_json['file']
                log_type = request_json['logType']

                normalized_entries, output_path = normalize_log_file(file_path, log_type)
                normalized_text = json.dumps(normalized_entries, default=str)

                # Count how many messages contain common error keywords
                from processing.error_detection import detect_errors
                combined_text = ' '.join(entry["message"] for entry in normalized_entries if "message" in entry)
                error_count = detect_errors(combined_text)

                result = {
                    "message": "File processed!",
                    "errorCount": error_count,
                    "normalizedText": normalized_text
                }

        # Save result to a temp file and return the path
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8") as tmp:
            json.dump(result, tmp, ensure_ascii=False, indent=2)
            print(tmp.name)  # ONLY output the filename

    except Exception as e:
        fallback = {
            "message": f"Error processing request: {str(e)}",
            "errorCount": 0,
            "normalizedText": "Error: Exception occurred.",
            "downloadPath": None
        }

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8") as tmp:
            json.dump(fallback, tmp, ensure_ascii=False, indent=2)
            print(tmp.name)

if __name__ == '__main__':
    main()

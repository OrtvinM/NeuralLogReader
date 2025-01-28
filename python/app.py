from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/detect', methods=['POST'])
def detect_errors():
    data = request.get_json()
    text = data.get('text', '')
    if not text:
        return jsonify(message='No text provided', errorCount=0)

    error_keywords = ["fatal", "error", "issue"]
    error_count = sum(text.lower().count(keyword) for keyword in error_keywords)

    return jsonify(message='Received!', errorCount=error_count)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)

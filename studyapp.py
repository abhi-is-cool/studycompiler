from flask import Flask, render_template, request, send_file, jsonify
from flask_cors import CORS
import fitz
from io import BytesIO
from openai import OpenAI

app = Flask(__name__)
CORS(app)

openai_client  = OpenAI.Client(api_key = "openai_api_key")

def extract_text_from_pdf(file_stream):
    doc = fitz.open(stream=file_stream.read(), filetype='pdf')
    return '\n'.join([page.get_text() for page in doc])




def extract_topics(content):
    prompt = f"From the following text, extract a list of major topics and subtopics. Respond in JSON format like this:\n\n" + \
             "{ \"topics\": [ { \"name\": \"Biology\", \"subtopics\": [\"Cells\", \"Photosynthesis\"] }, ... ] }\n\n" + \
             content[:4000] 
    chat_completion = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
        temperature=0.5
    )
    import json
    response_text = chat_completion.choices[0].message.content
    try:
        topics_json = json.loads(response_text)
        return topics_json.get("topics", [])
    except json.JSONDecodeError:
        return []


def generate_notes_for_topics(content, selected_topics):
    topic_list_str = ", ".join(t["name"] for t in selected_topics)
    prompt = f"Based on the following content, generate detailed notes for these topics and subtopics:\n{selected_topics}\n\nContent:{content[:6000]}" if topic else f"Generate detailed notes based on the following content: \n\n{content}"

    chat_completion = openai_client.chat.completions.create(
        model = "gpt-4",
        messages = [
            {"role": "user", "content": prompt}       
        ],
        max_tokens = 1500,
        temperature = 0.7                      
    )
    return chat_completion.choices[0].message.content


@app.route("/extract_topics", methods=["POST"])
def extract_topics_endpoint():

    file = request.files["file"]
    topic = request.form.get("topic")

    if not "file" and not topic:
        return jsonify({"error": "No file or topic provided"}), 400

    content = ""
    if file:
        content += extract_text_from_pdf(file)

    if not content and topic:
        content += topic

    try:
        notes = generate_notes(content, topic)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    file_stream = BytesIO()
    file_stream.write(notes.encode('utf-8'))
    file_stream.seek(0)
    return send_file(file_stream, as_attachment=True, download_name="notes.txt", mimetype="text/plain")

if __name__ == "__main__":
    app.run(debug=True)


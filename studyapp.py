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
    chat_completion = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
        temperature=0.5
        )
        # stuff needed here
    import json
    response_text = chat_completion.choices[0].message.content
    try:
        topics_json = json.loads(response_text)
        return topics_json.get("topics", [])
    except json.JSONDecodeError:
        return []
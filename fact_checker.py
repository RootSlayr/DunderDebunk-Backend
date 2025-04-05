import json
import re
from random import random
from flask import Blueprint, jsonify, request

import mysql.connector

from mysql.connector import pooling

import pathlib
import textwrap

import google.generativeai as genai

from IPython.display import display
from IPython.display import Markdown

def to_markdown(text):
  text = text.replace('•', '  *')
  return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

GOOGLE_API_KEY="AIzaSyD9Mnlksk7LO3DlzkzWi2_aMaCdos1fCZI"
genai.configure(api_key=GOOGLE_API_KEY)

generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-pro",
  generation_config=generation_config,
  system_instruction="You are given a series of text passages. Your task is to verify the authenticity of each part of the text based on general knowledge, factual accuracy, and plausibility.\n\nInstructions:\n\nMark the text segments as follows:\n\nIf a part is authentic or highly likely to be true, enclose it in square brackets → [text]\n\nIf a part is uncertain, partially credible, or unverifiable, enclose it in curly braces → {text}\n\nIf a part is false, misleading, or known to be fake, enclose it in vertical lines → |text|\n\nReturn the processed result as: {text:\"[authentic part] {uncertain part} |fake part|\", trust_score:XX}\n\nScoring Guide:\n\n90–100: Mostly or entirely true\n\n60–89: Contains a mix of truth and uncertainty\n\n30–59: Mostly uncertain or partially misleading\n\n0–29: Largely false or fabricated",
)

chat_session = model.start_chat(
  history=[
  ]
)
message = """

April 5, 2025 — Geneva, Switzerland

In a groundbreaking announcement today, scientists at the European Space Agency (ESA) claimed to have discovered a previously undetected "invisible moon" orbiting Earth. The object, temporarily named Luna Obscura, is said to be made of a form of dark matter that doesn't reflect light and is completely undetectable by traditional telescopes.

According to Dr. Martina Valenko, the lead physicist on the project, “This dark satellite has likely been orbiting Earth for thousands of years, explaining ancient myths about a ‘shadow moon’ that appears only during eclipses.”

While skeptics have pointed out the lack of direct evidence, ESA asserts that gravitational anomalies detected during recent lunar missions support the presence of Luna Obscura. The invisible moon is estimated to be about half the size of Mars and is responsible for recent fluctuations in Earth’s magnetic field — a phenomenon NASA has also independently confirmed.

In an unexpected twist, Tesla CEO Elon Musk announced plans to launch a crewed mission to the dark moon by 2027 using a new version of the Starship rocket, which is now reportedly powered by cold fusion — a technology once thought to be impossible.

Meanwhile, a NASA spokesperson denied knowledge of the object, stating, “There is no evidence of a second moon. ESA’s data may be misinterpreted due to recent solar activity. We advise caution before drawing conclusions.”

The discovery has sparked widespread excitement and confusion, with several online forums suggesting the moon may be linked to mysterious signals intercepted by SETI in early 2024 — signals previously dismissed as cosmic background noise."""
# response = chat_session.send_message(message)
#
# print(response.text)
# 创建连接池
dbconfig = {
    "host": "database-1.ct466iusq8wi.ap-southeast-2.rds.amazonaws.com",
    "user": "SunProtection",
    "password": "SunProtection12345",
    "database": "Dunder Debunk",
}

pool = pooling.MySQLConnectionPool(pool_name="mypool",
                                   pool_size=16,
                                   **dbconfig)

# 从连接池获取连接
# conn = pool.get_connection()
# cursor = conn.cursor()
# cursor.execute("SELECT * from questions;")
# print(cursor.fetchone())
#
# # 关闭连接（返回到池）
# cursor.close()
# conn.close()

# 创建蓝图对象
fact_checker_bp = Blueprint("fact_checker", __name__)


def google_fact_checker():
    pass

def strip_markdown_json_block(text):
    # 去掉开头的 ```json 或 ```，结尾的 ```
    return text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()


def parse_fact_check_response(raw_response):
    """Fallback parser for non-JSON formatted responses"""
    # Try original pattern for non-JSON formats
    text_pattern = r'{text:\s*"(.*?)"\s*,\s*trust_score:\s*(\d+)}'
    match = re.search(text_pattern, raw_response, re.DOTALL)

    if not match:
        # Try alternative pattern
        text_pattern = r'text:\s*"(.*?)"\s*,\s*trust_score:\s*(\d+)'
        match = re.search(text_pattern, raw_response, re.DOTALL)

    if match:
        # Extract text and score
        text_content = match.group(1)
        trust_score = int(match.group(2))

        # Create a proper JSON response
        return json.dumps({
            "text": text_content,
            "trust_score": trust_score
        }, ensure_ascii=False)
    else:
        return json.dumps({"error": "Could not parse response pattern", "raw": raw_response})


@fact_checker_bp.route("/upload", methods=["POST"])
def upload():
    json_param = request.get_json()
    text = json_param.get("text")
    session = json_param.get("session")

    try:
        # Get response from the model
        result = chat_session.send_message(text)
        stripped_text = strip_markdown_json_block(result.text)
        print("Stripped text:", stripped_text)

        # Direct JSON parsing - the response is already valid JSON
        try:
            # Parse the JSON to validate it
            json_obj = json.loads(stripped_text)

            # If we can parse it and it has the expected fields, return it directly
            if "text" in json_obj and "trust_score" in json_obj:
                return stripped_text, 200, {'Content-Type': 'application/json'}
            else:
                return jsonify({"error": "Response missing required fields"}), 400

        except json.JSONDecodeError as e:
            # Only if JSON parsing fails, try the regex approach
            print(f"JSON parse error: {e}")
            parsed_json = parse_fact_check_response(stripped_text)
            return parsed_json, 200, {'Content-Type': 'application/json'}

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error processing response: {e}")
        return jsonify({"error": str(e)}), 500
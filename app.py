from flask import Flask, jsonify
from flask_cors import CORS

import quiz

app = Flask(__name__)
app.register_blueprint(quiz.quiz_bp, url_prefix="/quiz")
CORS(app)


@app.route("/api/test", methods=["GET"])
def test():
    return jsonify(message="Testing Backend")

# def generate_a_token():
#


# @app.route("/requestToken", methods=["POST"])
# def requestToken():
#     token = generate_a_token()

if __name__ == "__main__":

    app.run(debug=True)

from flask import Flask, jsonify
from flask_cors import CORS
from courses import courses  # Import the courses list from the courses.py file

app = Flask(__name__)
CORS(app)


@app.route("/api/test", methods=["GET"])
def test():
    """Testing 1 2 3"""
    return jsonify(message="Testing Backend")


@app.route("/courses", methods=["GET"])
def get_courses():
    """
    Calls the courses Dictionary and returns it as a JSON object.
    This is used to display the courses on the frontend.
    The courses are stored in a list of dictionaries, where each dictionary contains the course id, name, and image path.
    """
    return jsonify(courses)


if __name__ == "__main__":
    app.run(debug=True)

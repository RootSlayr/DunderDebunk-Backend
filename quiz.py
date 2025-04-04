import random
from datetime import datetime
from urllib import request
from flask import make_response

from flask import request
from flask import Blueprint, jsonify

import mysql.connector
from mysql.connector import pooling

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
quiz_bp = Blueprint("quiz", __name__)


def generate_random_number(start=1, end=100):
    return random.randint(start, end)

def choosing_quiz_strategy():
    conn = pool.get_connection()
    cursor = conn.cursor()
    cursor.execute("select count(*) from quiz;")
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return generate_random_number(1, count)




@quiz_bp.route("/start", methods=["GET"])
def start():
    try:
        conn = pool.get_connection()
        cursor = conn.cursor()
        quiz_id = choosing_quiz_strategy()
        query = """
            SELECT * 
            FROM quiz 
            LEFT JOIN quiz_question ON quiz.quiz_id = quiz_question.quiz_id 
            LEFT JOIN questions ON quiz_question.question_id = questions.question_id 
            # left join question_selection on questions.question_id = question_selection.question_id 
            WHERE quiz.quiz_id = %s
            """
        cursor.execute(query, (quiz_id,))
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        cursor.close()
        conn.close()

        # Optionally, return results as list of dicts for readability
        structured_results = [dict(zip(columns, row)) for row in results]

        return jsonify(structured_results)

    except Exception as e:
        print(f"Error: {e}")
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        return make_response(jsonify({"error": "Failed to start quiz"}), 500)


@quiz_bp.route("/get_selections", methods=["GET"])
def get_selections():
    try:
        # Get question_id and quiz_id from request parameters
        question_id = request.args.get('question_id', type=int)
        # Validate that both parameters are provided
        if question_id is None:
            return jsonify({"error": "question_id is required"}), 400

        # Get connection from pool
        conn = pool.get_connection()
        cursor = conn.cursor(dictionary=True)  # Use dictionary cursor for JSON-friendly results

        # Query to get selections from question_selection table
        query = """
            SELECT * FROM question_selection 
            WHERE question_id = %s;
        """
        cursor.execute(query, (question_id,))

        # Fetch all results
        selections = cursor.fetchall()

        # Close cursor and release connection back to pool
        cursor.close()
        conn.close()

        return jsonify(selections)

    except Exception as e:
        # Handle any errors
        return jsonify({"error": str(e)}), 500


@quiz_bp.route("/submit", methods=["POST"])
def get_results():
    request_data = request.get_json()
    quiz_id = request_data.get("quiz_id")
    user_answers = request_data.get("answers")  # The entire JSON array is the user's answers

    correct_answers = 0
    all_answers = len(user_answers)

    try:
        conn = pool.get_connection()
        cursor = conn.cursor()

        # Get the correct answers for all questions in this quiz
        query_questions = """
        SELECT q.question_id, q.correct_answer 
        FROM questions q
        JOIN quiz_question qq ON q.question_id = qq.question_id
        WHERE qq.quiz_id = %s
        """
        cursor.execute(query_questions, (quiz_id,))
        question_results = cursor.fetchall()

        # Convert to dictionary for easier lookup
        correct_answer_dict = {row[0]: row[1] for row in question_results}

        # Compare user answers with correct answers
        for answer in user_answers:
            question_id = answer.get("question_id")
            user_selection = answer.get("user_answer")
            print(question_id, user_selection)
            print(correct_answer_dict[question_id])
            if question_id in correct_answer_dict and user_selection == correct_answer_dict[question_id]:
                print("正确")
                correct_answers += 1

        insert_query = "INSERT INTO quiz_record (session_id, quiz_id, time, correct_count) VALUES (%s, %s, %s, %s)"
        values = ('testing', quiz_id, datetime.now(), correct_answers)

        # Execute the query
        cursor.execute(insert_query, values)

        record_id = cursor.lastrowid
        # Save user selections to database
        for answer in user_answers:
            query_save = """
            INSERT INTO selection (record_id, question_id, selection)
            VALUES (%s, %s, %s)
            """
            cursor.execute(query_save, (record_id, answer.get("question_id"), answer.get("user_answer")))

        conn.commit()

        return jsonify({
            "correct_answers": correct_answers,
            "all_answers": all_answers,
            "score_percentage": round((correct_answers / all_answers) * 100, 2) if all_answers > 0 else 0
        })

    except Exception as e:
        # Handle any errors
        return jsonify({
            "error": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
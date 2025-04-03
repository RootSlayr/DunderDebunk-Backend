from random import random
from urllib import request

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
                                   pool_size=70,
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
quiz_bp = Blueprint("movie", __name__)


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
        # Fix the SQL query by specifying the join conditions
        query = """
            SELECT * 
            FROM quiz 
            LEFT JOIN quiz_question ON quiz.quiz_id = quiz_question.quiz_id 
            LEFT JOIN questions ON quiz_question.question_id = questions.question_id 
            WHERE quiz.quiz_id = %s
            """

        cursor.execute(query, (quiz_id,))

        # Fetch all results
        results = cursor.fetchall()

        # Get column names for better data handling
        columns = [desc[0] for desc in cursor.description]

        # Close cursor and connection
        cursor.close()
        conn.close()
        print(results)
        return jsonify(results)

    except Exception as e:
        print(f"Error: {e}")
        # Make sure to close connection in case of error
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        return None, None

@quiz_bp.route("/answer", methods=["POST"])
def answer():
    request_data = request.get_json()
    quiz_id = request_data["quiz_id"]
    selection = request_data["selection"]
    question_id = request_data["question_id"]
    record_id = request_data["record_id"]
    query = """
        insert into selection
        (question_id, record_id, selection) values (%s, %s, %s)
        """
    conn = pool.get_connection()
    cursor = conn.cursor()
    cursor.execute(query, (quiz_id, selection, question_id))
    return "ok"


@quiz_bp.route("/get_results", methods=["POST"])
def get_results():
    request_data = request.get_json()
    quiz_id = request_data["quiz_id"]
    record_id = request_data["record_id"]
    correct_answers = 0
    all_answers = 0
    conn = pool.get_connection()
    cursor = conn.cursor()
    query_questions = """
    select question_id, correct_answer from quiz left join quiz_question left join questions  where quiz_id = %s"""
    cursor.execute(query_questions, (quiz_id))
    all = cursor.fetchall()
    correct_result = []
    for row in all:
        correct_answers.append({row[0]:row[1]})


    query_selections = """
    select question_id,selection from quiz_record left join selection where record_id = %s;"""
    cursor.execute(query_selections, (record_id))
    all = cursor.fetchall()
    for row in all:
        if correct_result[row[0]] == row[1]:
            correct_answers +=1
        all_answers += 1

    return jsonify({
        "correct_answers": correct_answers,
        "all_answers": all_answers,
    })



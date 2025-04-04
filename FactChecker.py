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
fact_checker_bp = Blueprint("fact_checker", __name__)


def google_fact_checker():
    pass



@fact_checker_bp.route("/scan", methods=["GET"])
def scan():
    pass




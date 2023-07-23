import os
from psycopg2 import connect
from decouple import config


def create_db():
    file = os.path.dirname(__file__) + "db_file/creation.sql"

    conn = connect(
        host=config("DB_HOST"),
        dbname=config("DB_NAME"),
        user=config("DB_USER"),
        password=config("DB_PASS"),
        port=config("DB_PORT"),
    )

    cur = conn.cursor()

    try:
        with open(file, "r") as f:
            sql = f.read()
            cur.execute(sql)
            conn.commit()
    except Exception as e:
        print("file already executed")
        conn.rollback()
    cur.close()
    conn.close()

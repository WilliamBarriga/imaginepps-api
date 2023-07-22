from fastapi.exceptions import HTTPException

# Psycopg2
import psycopg2
from psycopg2.extensions import connection
from psycopg2.errors import InFailedSqlTransaction

# Env
from decouple import config


class DBManager:
    def __init__(self) -> None:
        self.conn = self.connect()

    def __del__(self) -> None:
        self.conn.close()

    def _check_connection(func):
        def wrapper(self, *args, **kwargs):
            if self.conn.closed:
                self.conn = self.connect()
            try:
                return func(self, *args, **kwargs)
            except InFailedSqlTransaction:
                self.conn.rollback()
                self.conn.close()
                self.conn = self.connect()
                return func(self, *args, **kwargs)
            except Exception as e:
                if not self.conn.closed:
                    self.conn.rollback()
                    self.conn.close()
                self.conn = self.connect()
                detail = "Something went wrong with the database: "
                raise HTTPException(status_code=500, detail=detail + str(e))

        return wrapper

    def connect(self) -> connection:
        """Connect to database"""
        conn = psycopg2.connect(
            host=config("DB_HOST"),
            dbname=config("DB_NAME"),
            user=config("DB_USER"),
            password=config("DB_PASS"),
            port=config("DB_PORT"),
        )
        return conn

    @_check_connection
    def fetch_one(self, stm: str) -> dict:
        """Fetch one row"""
        cur = self.conn.cursor()
        cur.execute(stm)
        if cur.rowcount > 0:
            columns = [column[0] for column in cur.description]
            data = dict(zip(columns, cur.fetchone()))
            cur.close()
            return data
        cur.close()

    @_check_connection
    def fetch_all(self, stm: str) -> list:
        """Fetch all rows"""
        cur = self.conn.cursor()
        cur.execute(stm)
        if cur.rowcount > 0:
            columns = [column[0] for column in cur.description]
            data = [dict(zip(columns, row)) for row in cur.fetchall()]
            cur.close()
            return data
        cur.close()

    @_check_connection
    def execute_sp(self, sp: str, *args: str) -> dict:
        """Execute stored procedure

        Args:
            sp (str): Stored procedure name
            args (str): Arguments for stored procedure (value::type)

        Returns:
            dict[str, str]: Message
        """

        cur = self.conn.cursor()
        stm = f"select * from {sp}({', '.join(args)})"
        cur.execute(stm)
        self.conn.commit()
        columns = []

        for column in cur.description:
            if column[0].startswith("_"):
                columns.append(column[0][1:])
            else:
                columns.append(column[0])

        data = [dict(zip(columns, row)) for row in cur.fetchall()]
        cur.close()
        if len(data) == 1:
            return data[0]
        return data

db = DBManager()
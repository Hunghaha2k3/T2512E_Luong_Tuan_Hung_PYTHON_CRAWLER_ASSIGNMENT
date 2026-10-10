import mysql.connector
from mysql.connector import Error

class MySqlHandler:
    def __init__(self, config):
        self.config = {**config, "charset": "utf8mb4"}

    def get_connection(self):
        try:
            return mysql.connector.connect(**self.config)
        except Error as e:
            print(f"Lỗi kết nối MySQL: {e}")
            return None

    def query(self, sql, params=None):
    # SELECT -> list[dict]. Lỗi -> []
        conn = self.get_connection()
        if conn is None:
            return []
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, params or ())
            return cursor.fetchall()
        except Error as e:
            print(f"Lỗi truy vấn: {e}")
            return []
        finally:
            conn.close()
    
    def execute(self, sql, params=None):
    # INSERT/UPDATE/DELETE -> số dòng bị ảnh hưởng. Lỗi -> -1
        conn = self.get_connection()
        if conn is None:
            return -1
        try: 
            cursor = conn.cursor()
            cursor.execute(sql, params or ())
            conn.commit()
            return cursor.rowcount
        except Error as e:
            print(f"Lỗi thực thi lệnh: {e}")
            conn.rollback()
            return -1
        finally:
            conn.close()



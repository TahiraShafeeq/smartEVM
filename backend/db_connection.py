
import oracledb

def get_connection():
    try:
        connection = oracledb.connect(
            user="evm_owner",
            password="Tahira_shafeeq",
            dsn="localhost:1521/FREEPDB1"
        )
        return connection
    except Exception as e:
        print("Connection has failed:", e)
        return None

if __name__ == "__main__":
    conn = get_connection()
    if conn:
        print("Success! Python is now talking to Oracle.")
        conn.close()
import mysql.connector

def __get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='face_project'
    )
    return connection

# Add this function to test the connection
def test_connection():
    try:
        conn = __get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE();")
        db_name = cursor.fetchone()
        print(f"Connected to database: {db_name[0]}")
        cursor.close()
        conn.close()
        return True
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return False

if __name__ == "__main__":
    test_connection()
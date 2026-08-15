from db_connection import get_connection


def create_user(username, password_hash, role_id):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO Users (username,password_hash,role_id)
        VALUES (:1,:2,:3)
        """, [username, password_hash, role_id])

        conn.commit()

    except Exception as e:
        print("Error creating user:", e)
        conn.rollback()

    finally:
        conn.commit()
        cursor.close()
        conn.close()


def get_users():

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Users")

        return cursor.fetchall()

    finally:
        cursor.close()
        conn.close()


def update_user(user_id, username, password_hash, role_id):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE Users
        SET username=:1, password_hash=:2, role_id=:3
        WHERE user_id=:4
        """, [username, password_hash, role_id, user_id])

        conn.commit()

    except Exception as e:
        print("Error updating user:", e)
        conn.rollback()

    finally:
        cursor.close()
        conn.close()


def delete_user(user_id):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM Projects WHERE manager_id=:1",[user_id])
        if cursor.fetchone()[0] > 0:
            print("Cannot delete user. User manages projects.")
            return

        cursor.execute("SELECT COUNT(*) FROM Tasks WHERE assigned_to=:1",[user_id])
        if cursor.fetchone()[0] > 0:
            print("Cannot delete user. User assigned to tasks.")
            return

        cursor.execute("DELETE FROM Users WHERE user_id=:1",[user_id])

        conn.commit()

    except Exception as e:
        print("Error deleting user:", e)
        conn.rollback()

    finally:
        cursor.close()
        conn.close()
import oracledb
from db_connection import get_connection


def create_task(sprint_id, assigned_to, external_id, description, status, story_points):
    """Insert task and return the new task_id — CRITICAL for jira_importer."""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        tid_var = cursor.var(oracledb.NUMBER)
        cursor.execute("""
            INSERT INTO Tasks
                (sprint_id, assigned_to, external_id, task_description, status, story_points)
            VALUES (:1, :2, :3, :4, :5, :6)
            RETURNING task_id INTO :7
        """, [sprint_id, assigned_to, external_id, description, status, story_points, tid_var])
        conn.commit()
        return int(tid_var.getvalue()[0])
    except Exception as e:
        print("Error creating task:", e)
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()


def get_tasks(sprint_id=None):
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        if sprint_id:
            cursor.execute(
                "SELECT * FROM Tasks WHERE sprint_id=:1 ORDER BY task_id",
                [sprint_id]
            )
        else:
            cursor.execute("SELECT * FROM Tasks ORDER BY task_id")
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching tasks:", e)
        return []
    finally:
        cursor.close()
        conn.close()


def update_task(task_id, sprint_id, assigned_to, external_id, description, status, story_points):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Tasks
            SET sprint_id=:1, assigned_to=:2, external_id=:3,
                task_description=:4, status=:5, story_points=:6
            WHERE task_id=:7
        """, [sprint_id, assigned_to, external_id, description, status, story_points, task_id])
        conn.commit()
        return True
    except Exception as e:
        print("Error updating task:", e)
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def delete_task(task_id):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Metrics WHERE task_id=:1", [task_id])
        cursor.execute("DELETE FROM Tasks WHERE task_id=:1", [task_id])
        conn.commit()
        return True
    except Exception as e:
        print("Error deleting task:", e)
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

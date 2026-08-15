import oracledb
from db_connection import get_connection


def create_metric(task_id, tester_id, critical_bugs, major_bugs, minor_bugs,
                  bug_count, code_coverage, tech_debt_hours, calculated_qpi):
    """Insert metric and return the new metric_id."""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        mid_var = cursor.var(oracledb.NUMBER)
        cursor.execute("""
            INSERT INTO Metrics
                (task_id, tester_id, critical_bugs, major_bugs, minor_bugs,
                 bug_count, code_coverage, tech_debt_hours, calculated_qpi)
            VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9)
            RETURNING metric_id INTO :10
        """, [task_id, tester_id, critical_bugs, major_bugs, minor_bugs,
              bug_count, code_coverage, tech_debt_hours, calculated_qpi, mid_var])
        conn.commit()
        return int(mid_var.getvalue()[0])
    except Exception as e:
        print("Error creating metric:", e)
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()


def get_metrics(task_id=None):
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        if task_id:
            cursor.execute("SELECT * FROM Metrics WHERE task_id=:1", [task_id])
        else:
            cursor.execute("SELECT * FROM Metrics ORDER BY metric_id")
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching metrics:", e)
        return []
    finally:
        cursor.close()
        conn.close()


def delete_metric(metric_id):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Metrics WHERE metric_id=:1", [metric_id])
        conn.commit()
        return True
    except Exception as e:
        print("Error deleting metric:", e)
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

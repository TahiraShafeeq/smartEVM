import oracledb
from datetime import datetime, date
from db_connection import get_connection


def _parse_date(d):
    """
    Convert a date string (any common format) to a Python date object.
    Oracle's oracledb driver accepts Python date objects natively —
    this avoids ORA-01861 (literal does not match format string).

    Accepts: '2025-01-01', '01-JAN-2025', '2025/01/01', None
    """
    if d is None:
        return None
    if isinstance(d, (date, datetime)):
        return d
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d",
                "%d-%b-%Y", "%d-%B-%Y"):
        try:
            return datetime.strptime(str(d), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: '{d}'. Use format YYYY-MM-DD e.g. '2025-01-01'")


def create_project(name, budget, start_date, end_date, manager_id):
    """Insert project and return the new project_id assigned by Oracle."""
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        pid_var = cursor.var(oracledb.NUMBER)
        cursor.execute("""
            INSERT INTO Projects (project_name, total_budget, start_date, end_date, manager_id)
            VALUES (:1, :2, :3, :4, :5)
            RETURNING project_id INTO :6
        """, [name, budget, _parse_date(start_date), _parse_date(end_date),
              manager_id, pid_var])
        conn.commit()
        return int(pid_var.getvalue()[0])
    except ValueError as ve:
        print("Date format error:", ve)
        return None
    except Exception as e:
        print("Error creating project:", e)
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()


def get_projects():
    conn = get_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Projects ORDER BY project_id")
        return cursor.fetchall()
    except Exception as e:
        print("Error fetching projects:", e)
        return []
    finally:
        cursor.close()
        conn.close()


def get_project_by_id(project_id):
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Projects WHERE project_id=:1", [project_id])
        return cursor.fetchone()
    except Exception as e:
        print("Error fetching project:", e)
        return None
    finally:
        cursor.close()
        conn.close()


def update_project(project_id, name, budget, start_date, end_date, manager_id):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Projects
            SET project_name=:1, total_budget=:2, start_date=:3,
                end_date=:4, manager_id=:5
            WHERE project_id=:6
        """, [name, budget, _parse_date(start_date), _parse_date(end_date),
              manager_id, project_id])
        conn.commit()
        return True
    except Exception as e:
        print("Error updating project:", e)
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def delete_project(project_id):
    conn = get_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM Metrics WHERE task_id IN (
                SELECT task_id FROM Tasks WHERE sprint_id IN (
                    SELECT sprint_id FROM Sprints WHERE project_id=:1))
        """, [project_id])
        cursor.execute("""
            DELETE FROM Tasks WHERE sprint_id IN (
                SELECT sprint_id FROM Sprints WHERE project_id=:1)
        """, [project_id])
        cursor.execute("DELETE FROM Sprints WHERE project_id=:1", [project_id])
        cursor.execute("DELETE FROM EVM_History WHERE project_id=:1", [project_id])
        cursor.execute("DELETE FROM Projects WHERE project_id=:1", [project_id])
        conn.commit()
        return True
    except Exception as e:
        print("Error deleting project:", e)
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

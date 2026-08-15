

from db_connection import get_connection
import oracledb
import hashlib
from datetime import date


def _hash_password(plain: str) -> str:
    return hashlib.sha256(plain.encode()).hexdigest()


def bulk_jira_github_ingestion():
    conn = get_connection()
    if not conn:
        print("❌ Database connection failed"); return

    cursor = conn.cursor()
    try:
        print("🚀 Starting JIRA + GitHub Data Ingestion...\n")

        # ── 1. Roles ──────────────────────────────────────────────────────────
        for r in ["Admin", "Project Manager", "Team Member", "Finance", "QA Tester"]:
            cursor.execute("SELECT COUNT(*) FROM Roles WHERE role_name = :1", [r])
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO Roles (role_name) VALUES (:1)", [r])
        print("✅ Roles verified")

        # ── 2. Users ──────────────────────────────────────────────────────────
        users = [
            ("pm_sarah",  "pmpass001", "Project Manager"),
            ("pm_ali",    "pmpass002", "Project Manager"),
            ("dev_hamza", "devpass01", "Team Member"),
            ("dev_zara",  "devpass02", "Team Member"),
            ("dev_usman", "devpass03", "Team Member"),
            ("qa_fatima", "qapass001", "QA Tester"),
        ]
        user_map = {}
        for uname, pwd, role in users:
            cursor.execute("SELECT user_id FROM Users WHERE username = :1", [uname])
            row = cursor.fetchone()
            if row:
                user_map[uname] = row[0]
            else:
                uid_var = cursor.var(oracledb.NUMBER)
                cursor.execute("""
                    INSERT INTO Users (username, password_hash, role_id)
                    VALUES (:1, :2, (SELECT role_id FROM Roles WHERE role_name = :3))
                    RETURNING user_id INTO :4
                """, [uname, _hash_password(pwd), role, uid_var])
                user_map[uname] = int(uid_var.getvalue()[0])
        print("✅ Users ready")

        # ── 3. Projects ───────────────────────────────────────────────────────
        projects = [
            ("SmartEVM Platform v2.0",   250000, "pm_sarah", date(2025, 1, 1),  date(2025, 6, 30)),
            ("E-Commerce Portal Revamp", 180000, "pm_ali",   date(2025, 2, 1),  date(2025, 7, 31)),
            ("Legacy System Migration",   95000, "pm_sarah", date(2025, 1, 15), date(2025, 5, 15)),
        ]
        project_ids = []
        for pname, budget, pm, s, e in projects:
            cursor.execute("SELECT project_id FROM Projects WHERE project_name = :1", [pname])
            row = cursor.fetchone()
            if row:
                project_ids.append(row[0])
            else:
                pid_var = cursor.var(oracledb.NUMBER)
                cursor.execute("""
                    INSERT INTO Projects (project_name, total_budget, manager_id, start_date, end_date)
                    VALUES (:1, :2, :3, :4, :5) RETURNING project_id INTO :6
                """, [pname, budget, user_map[pm], s, e, pid_var])
                project_ids.append(int(pid_var.getvalue()[0]))
        print("✅ Projects ready")

        # ── 4. Sprints ────────────────────────────────────────────────────────
        sprint_map = {}
        sprint_defs = {
            0: [
                (1, "Sprint 1 - Foundation & Auth",   date(2025, 1, 1),  date(2025, 1, 14), 35000),
                (2, "Sprint 2 - EVM Core Engine",     date(2025, 1, 15), date(2025, 1, 28), 55000),
                (3, "Sprint 3 - Dashboard & Reports", None,              None,               60000),
            ],
            1: [
                (1, "Sprint 1 - Product Catalog",     date(2025, 2, 1),  date(2025, 2, 14), 40000),
                (2, "Sprint 2 - Cart & Checkout",     date(2025, 2, 15), date(2025, 2, 28), 50000),
                (3, "Sprint 3 - Payment Gateway",     None,              None,               45000),
            ],
            2: [
                (1, "Sprint 1 - Database Extraction", date(2025, 1, 15), date(2025, 1, 31), 28000),
                (2, "Sprint 2 - API Refactoring",     date(2025, 2, 1),  date(2025, 2, 28), 35000),
                (3, "Sprint 3 - UAT & Deployment",    date(2025, 3, 1),  date(2025, 3, 31), 32000),
            ],
        }
        for idx, sprint_list in sprint_defs.items():
            pid = project_ids[idx]
            for sno, sname, ss, se, pv in sprint_list:
                cursor.execute(
                    "SELECT sprint_id FROM Sprints WHERE sprint_name = :1 AND project_id = :2",
                    [sname, pid]
                )
                row = cursor.fetchone()
                if row:
                    sprint_map[sname] = row[0]
                else:
                    sid_var = cursor.var(oracledb.NUMBER)
                    cursor.execute("""
                        INSERT INTO Sprints
                            (project_id, sprint_no, sprint_name, start_date, end_date, planned_value)
                        VALUES (:1, :2, :3, :4, :5, :6)
                        RETURNING sprint_id INTO :7
                    """, [pid, sno, sname, ss, se, pv, sid_var])
                    sprint_map[sname] = int(sid_var.getvalue()[0])
        print("✅ Sprints ready")


        issues = [
            ("Sprint 1 - Foundation & Auth",   "SEVM-101", "JWT-based user authentication",          "Done",        8,  "dev_hamza", "qa_fatima", 0, 1, 2, 92.5,  3.0,  96.50),
            ("Sprint 1 - Foundation & Auth",   "SEVM-102", "Oracle DB connection pool setup",        "Done",        5,  "dev_zara",  "qa_fatima", 0, 0, 1, 95.0,  1.0,  99.00),
            ("Sprint 1 - Foundation & Auth",   "SEVM-103", "Role-based access control middleware",   "Done",        8,  "dev_usman", "qa_fatima", 0, 1, 1, 88.0,  4.0,  93.60),
            ("Sprint 2 - EVM Core Engine",     "SEVM-201", "EVM calculator module (CPI/SPI/EAC)",   "Done",        13, "dev_hamza", "qa_fatima", 0, 2, 3, 85.0,  6.0,  89.00),
            ("Sprint 2 - EVM Core Engine",     "SEVM-202", "QPI scoring engine",                    "Done",        8,  "dev_zara",  "qa_fatima", 0, 0, 2, 90.0,  2.0,  96.00),
            ("Sprint 2 - EVM Core Engine",     "SEVM-203", "EVM history snapshot API",              "In Progress", 8,  "dev_usman", "qa_fatima", 1, 1, 2, 65.0,  8.0,  72.00),
            ("Sprint 3 - Dashboard & Reports", "SEVM-301", "Vue.js EVM dashboard",                  "To Do",       13, "dev_hamza", None,        0, 0, 0, 0.0,   0.0,  100.0),
            ("Sprint 1 - Product Catalog",     "EC-101",   "Product listing with filters",          "Done",        13, "dev_hamza", "qa_fatima", 1, 2, 4, 75.0,  8.0,  76.00),
            ("Sprint 1 - Product Catalog",     "EC-102",   "Product detail page",                   "Done",        8,  "dev_usman", "qa_fatima", 0, 3, 2, 70.0,  10.0, 77.00),
            ("Sprint 2 - Cart & Checkout",     "EC-201",   "Shopping cart module",                  "In Progress", 8,  "dev_zara",  "qa_fatima", 0, 1, 3, 60.0,  5.0,  83.00),
            ("Sprint 1 - Database Extraction", "LM-101",   "Extract legacy Oracle tables",          "Done",        21, "dev_usman", "qa_fatima", 2, 5, 8, 55.0,  22.0, 46.40),
            ("Sprint 2 - API Refactoring",     "LM-201",   "Refactor SOAP to REST",                 "In Progress", 21, "dev_hamza", "qa_fatima", 3, 4, 6, 48.0,  35.0, 36.60),
            ("Sprint 3 - UAT & Deployment",    "LM-301",   "Deploy to Oracle Cloud + UAT",          "In Progress", 13, "dev_zara",  "qa_fatima", 1, 3, 5, 60.0,  18.0, 58.40),
        ]

        for row in issues:
            sname, ext_id, desc, status, pts, dev, tester, crit, maj, mino, cov, debt, qpi = row

            # Skip if task already exists (idempotent re-run)
            cursor.execute("SELECT task_id FROM Tasks WHERE external_id = :1", [ext_id])
            if cursor.fetchone():
                continue

            # ── Insert Task ──────────────────────────────────────────────────
            tid_var = cursor.var(oracledb.NUMBER)
            cursor.execute("""
                INSERT INTO Tasks
                    (sprint_id, assigned_to, external_id, task_description, status, story_points)
                VALUES (:1, :2, :3, :4, :5, :6)
                RETURNING task_id INTO :7
            """, [
                sprint_map[sname],
                user_map.get(dev),
                ext_id,
                desc,
                status,
                pts,
                tid_var
            ])
            tid = int(tid_var.getvalue()[0])

            # ── Insert Metric ────────────────────────────────────────────────
            # FIX: bug_count column was missing from INSERT — added here.
            # bug_count = critical + major + minor (computed, not stored separately in tuple)
            bug_count = crit + maj + mino

            cursor.execute("""
                INSERT INTO Metrics
                    (task_id, tester_id, critical_bugs, major_bugs, minor_bugs,
                     bug_count, code_coverage, tech_debt_hours, calculated_qpi)
                VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9)
            """, [
                tid,
                user_map.get(tester) if tester else None,
                crit,
                maj,
                mino,
                bug_count,          # FIX: was missing entirely
                cov,
                debt,
                qpi
            ])

        print("✅ Tasks + Metrics inserted\n")

        print("📌 GitHub Simulation: 47 commits | 12 PRs merged | Coverage 65%→87%")
        conn.commit()
        print("\n🎉 SUCCESS! Database fully populated.")

    except oracledb.IntegrityError as e:
        print(f"❌ Integrity Error: {e}")
        conn.rollback()
    except oracledb.DatabaseError as e:
        print(f"❌ DB Error: {e}")
        conn.rollback()
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    bulk_jira_github_ingestion()

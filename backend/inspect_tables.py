
import sqlite3

conn = sqlite3.connect(
    r"D:\new_project\project\smart_expenses1.db"
)

try:
    print("RISK FLAGS:")
    print(conn.execute(
        "PRAGMA table_info(RISK_FLAGS)"
    ).fetchall())

    print("\nAPPROVALS:")
    print(conn.execute(
        "PRAGMA table_info(APPROVALS)"
    ).fetchall())

    print("\nEXPENSE TABLE RULES:")
    result = conn.execute(
        "SELECT sql FROM sqlite_master "
        "WHERE type='table' AND name='EXPENSES'"
    ).fetchone()

    print(result)

finally:
    conn.close()

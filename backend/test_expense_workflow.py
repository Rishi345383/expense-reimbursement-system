import os
import shutil
import sqlite3
import tempfile

from app.database import DATABASE_NAME
from app.services.expense_service import submit_expense, list_expenses, review_expense, mark_reimbursement_paid


def add_user(conn, user_id, username, role):
    conn.execute(
        "INSERT INTO USER (USER_ID, USERNAME, PASSWORD, ROLE, STATUS, CREATED_AT) VALUES (?, ?, ?, ?, 'ACTIVE', datetime('now'))",
        (user_id, username, 'temporary-test-password', role)
    )


def main():
    temp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp.close()
    try:
        shutil.copy2(DATABASE_NAME, temp.name)
        conn = sqlite3.connect(temp.name)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        manager_id = conn.execute('SELECT COALESCE(MAX(USER_ID), 0) + 1 FROM USER').fetchone()[0]
        finance_id = manager_id + 1
        add_user(conn, manager_id, 'workflow_manager', 'MANAGER')
        add_user(conn, finance_id, 'workflow_finance', 'FINANCE')
        conn.commit()

        expense_id = submit_expense(conn, 2, 1, '2026-10-30', 450.00, 'Workflow test meal', 'receipt-test')
        print('Submitted:', expense_id, 'PENDING')
        assert any(row['EXPENSE_ID'] == expense_id for row in list_expenses(conn, 2))
        print('Employee can list own expense: PASS')

        result = review_expense(conn, expense_id, manager_id, 'APPROVED', 'Looks good')
        print('Manager approval:', result['status'])
        assert result['reimbursement_id'] is not None

        paid = mark_reimbursement_paid(conn, result['reimbursement_id'], finance_id, 'Bank transfer', 'TEST-001')
        assert paid['status'] == 'PAID'
        print('Finance marks reimbursement paid: PASS')
        print('End-to-end workflow: PASS')
        conn.close()
    finally:
        if os.path.exists(temp.name):
            os.remove(temp.name)


if __name__ == '__main__':
    main()

import os
import shutil
import sqlite3
import tempfile

from app.database import DATABASE_NAME
from app.services.expense_service import (
    approve_reimbursement, create_expense_draft, get_expense_audit,
    list_expenses, mark_reimbursement_paid, review_expense, submit_draft,
)


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

        expense_id = create_expense_draft(conn, 2, 1, '2026-10-30', 450.00, 'Workflow test meal', 'receipt-test')
        assert conn.execute('SELECT STATUS FROM EXPENSES WHERE EXPENSE_ID=?', (expense_id,)).fetchone()[0] == 'DRAFT'
        print('Create draft: PASS')
        submit_draft(conn, expense_id, 2)
        assert conn.execute('SELECT STATUS FROM EXPENSES WHERE EXPENSE_ID=?', (expense_id,)).fetchone()[0] == 'SUBMITTED'
        assert any(row['EXPENSE_ID'] == expense_id for row in list_expenses(conn, 2))
        print('Submit and employee list: PASS')

        result = review_expense(conn, expense_id, manager_id, 'APPROVED', 'Looks good')
        assert result['status'] == 'MANAGER_APPROVED'
        finance = approve_reimbursement(conn, result['reimbursement_id'], finance_id, 'Policy checked')
        assert finance['status'] == 'FINANCE_APPROVED'
        paid = mark_reimbursement_paid(conn, result['reimbursement_id'], finance_id, 'Bank transfer', 'TEST-001')
        assert paid['status'] == 'PAID'
        print('Manager approval, finance approval, and payment: PASS')

        history = get_expense_audit(conn, expense_id, 2)
        actions = [row['ACTION'] for row in history]
        assert actions == ['DRAFT_CREATED', 'SUBMITTED', 'MANAGER_APPROVED', 'FINANCE_APPROVED', 'REIMBURSEMENT_PAID']
        print('Audit trail: PASS')
        conn.close()
        print('End-to-end workflow: PASS')
    finally:
        if os.path.exists(temp.name):
            os.remove(temp.name)


if __name__ == '__main__':
    main()

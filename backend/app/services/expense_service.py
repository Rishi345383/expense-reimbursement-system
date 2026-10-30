from datetime import date


def _audit(conn, user_id, action, expense_id, old_status, new_status):
    conn.execute(
        """INSERT INTO AUDIT_LOGS
           (USER_ID, ACTION, ENTITY, ENTITY_ID, OLD_VALUE, NEW_VALUE, TIMESTAMP)
           VALUES (?, ?, 'EXPENSE', ?, ?, ?, datetime('now'))""",
        (user_id, action, expense_id, old_status, new_status)
    )


def _save_expense(conn, user_id, category_id, expense_date, amount, description, receipt_reference, status):
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise ValueError("Amount must be a number")
    if amount <= 0:
        raise ValueError("Amount must be greater than zero")
    try:
        date.fromisoformat(str(expense_date))
    except ValueError:
        raise ValueError("Expense date must use YYYY-MM-DD")
    description = str(description or "").strip()
    if not description:
        raise ValueError("Description is required")
    employee = conn.execute("SELECT EMPLOYEE_ID FROM EMPLOYEES WHERE USER_ID = ?", (user_id,)).fetchone()
    if employee is None:
        raise LookupError("Employee profile not found")
    policy = conn.execute("SELECT MAX_AMOUNT, DAILY_LIMIT, RECEIPT_REQUIRED FROM EXPENSE_POLICIES WHERE CATEGORY_ID = ?", (category_id,)).fetchone()
    if policy is None:
        raise LookupError("Expense category or policy not found")
    if policy["RECEIPT_REQUIRED"] and not receipt_reference:
        raise ValueError("A receipt reference is required for this category")
    daily_total = conn.execute(
        """SELECT COALESCE(SUM(AMOUNT), 0) FROM EXPENSES
           WHERE EMPLOYEE_ID = ? AND EXPENSE_DATE = ? AND STATUS NOT IN ('DRAFT', 'REJECTED')""",
        (employee["EMPLOYEE_ID"], expense_date)
    ).fetchone()[0]
    policy_status = "NON_COMPLIANT" if amount > policy["MAX_AMOUNT"] or daily_total + amount > policy["DAILY_LIMIT"] else "COMPLIANT"
    cursor = conn.execute(
        """INSERT INTO EXPENSES (EMPLOYEE_ID, CATEGORY_ID, EXPENSE_DATE, SUBMITTED_AT, AMOUNT,
           DESCRIPTION, RECEIPT_REFERENCE, POLICY_STATUS, RISK_SCORE, STATUS)
           VALUES (?, ?, ?, datetime('now'), ?, ?, ?, ?, 0, ?)""",
        (employee["EMPLOYEE_ID"], category_id, expense_date, amount, description, receipt_reference, policy_status, status)
    )
    action = "DRAFT_CREATED" if status == "DRAFT" else "SUBMITTED"
    _audit(conn, user_id, action, cursor.lastrowid, None, status)
    conn.commit()
    return cursor.lastrowid


def create_expense_draft(conn, user_id, category_id, expense_date, amount, description, receipt_reference=None):
    return _save_expense(conn, user_id, category_id, expense_date, amount, description, receipt_reference, "DRAFT")


def submit_expense(conn, user_id, category_id, expense_date, amount, description, receipt_reference=None):
    return _save_expense(conn, user_id, category_id, expense_date, amount, description, receipt_reference, "SUBMITTED")


def submit_draft(conn, expense_id, user_id):
    employee = conn.execute("SELECT EMPLOYEE_ID FROM EMPLOYEES WHERE USER_ID = ?", (user_id,)).fetchone()
    if employee is None:
        raise LookupError("Employee profile not found")
    expense = conn.execute("SELECT STATUS FROM EXPENSES WHERE EXPENSE_ID = ? AND EMPLOYEE_ID = ?", (expense_id, employee["EMPLOYEE_ID"])).fetchone()
    if expense is None:
        raise LookupError("Expense not found")
    if expense["STATUS"] != "DRAFT":
        raise ValueError("Only draft expenses can be submitted")
    conn.execute("UPDATE EXPENSES SET STATUS = 'SUBMITTED' WHERE EXPENSE_ID = ?", (expense_id,))
    _audit(conn, user_id, "SUBMITTED", expense_id, "DRAFT", "SUBMITTED")
    conn.commit()
    return {"expense_id": expense_id, "status": "SUBMITTED"}


def list_expenses(conn, user_id):
    user = conn.execute("SELECT ROLE FROM USER WHERE USER_ID = ?", (user_id,)).fetchone()
    if user is None:
        raise LookupError("User not found")
    if user["ROLE"] == "EMPLOYEE":
        employee = conn.execute("SELECT EMPLOYEE_ID FROM EMPLOYEES WHERE USER_ID = ?", (user_id,)).fetchone()
        if employee is None:
            raise LookupError("Employee profile not found")
        rows = conn.execute("""SELECT E.*, C.CATEGORY_NAME FROM EXPENSES E
            JOIN EXPENSE_CATEGORIES C ON E.CATEGORY_ID = C.CATEGORY_ID
            WHERE E.EMPLOYEE_ID = ? ORDER BY E.EXPENSE_ID DESC""", (employee["EMPLOYEE_ID"],)).fetchall()
    elif user["ROLE"] in ("MANAGER", "FINANCE", "ADMIN"):
        rows = conn.execute("""SELECT E.*, C.CATEGORY_NAME FROM EXPENSES E
            JOIN EXPENSE_CATEGORIES C ON E.CATEGORY_ID = C.CATEGORY_ID
            ORDER BY E.EXPENSE_ID DESC""").fetchall()
    else:
        raise PermissionError("This account cannot view expenses")
    return [dict(row) for row in rows]


def _approval(conn, expense_id, approver_id, level, decision, comments):
    approval_id = conn.execute("SELECT COALESCE(MAX(APPROVAL_ID), 0) + 1 FROM APPROVALS").fetchone()[0]
    conn.execute("""INSERT INTO APPROVALS
        (APPROVAL_ID, EXPENSE_ID, APPROVER_ID, APPROVAL_LEVEL, DECISION, COMMENTS, APPROVAL_DATE)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))""",
        (approval_id, expense_id, approver_id, level, decision, str(comments or "")))


def review_expense(conn, expense_id, approver_id, decision, comments=""):
    user = conn.execute("SELECT ROLE FROM USER WHERE USER_ID = ?", (approver_id,)).fetchone()
    if user is None:
        raise LookupError("Approver not found")
    if user["ROLE"] not in ("MANAGER", "ADMIN"):
        raise PermissionError("A manager account is required")
    decision = str(decision or "").upper()
    if decision not in ("APPROVED", "REJECTED"):
        raise ValueError("Decision must be APPROVED or REJECTED")
    expense = conn.execute("SELECT * FROM EXPENSES WHERE EXPENSE_ID = ?", (expense_id,)).fetchone()
    if expense is None:
        raise LookupError("Expense not found")
    if expense["STATUS"] not in ("SUBMITTED", "PENDING"):
        raise ValueError("Only submitted expenses can be reviewed")
    status = "MANAGER_APPROVED" if decision == "APPROVED" else "REJECTED"
    _approval(conn, expense_id, approver_id, "MANAGER", decision, comments)
    conn.execute("UPDATE EXPENSES SET STATUS = ? WHERE EXPENSE_ID = ?", (status, expense_id))
    reimbursement_id = None
    if decision == "APPROVED":
        cursor = conn.execute("""INSERT INTO REIMBURSEMENTS
            (EXPENSE_ID, EMPLOYEE_ID, CLAIMED_AMOUNT, APPROVED_AMOUNT, REQUESTED_DATE, STATUS)
            VALUES (?, ?, ?, ?, date('now'), 'PENDING')""",
            (expense_id, expense["EMPLOYEE_ID"], expense["AMOUNT"], expense["AMOUNT"]))
        reimbursement_id = cursor.lastrowid
    action = "MANAGER_APPROVED" if decision == "APPROVED" else "MANAGER_REJECTED"
    _audit(conn, approver_id, action, expense_id, expense["STATUS"], status)
    conn.commit()
    return {"expense_id": expense_id, "status": status, "reimbursement_id": reimbursement_id}


def approve_reimbursement(conn, reimbursement_id, finance_user_id, comments=""):
    user = conn.execute("SELECT ROLE FROM USER WHERE USER_ID = ?", (finance_user_id,)).fetchone()
    if user is None:
        raise LookupError("Finance user not found")
    if user["ROLE"] not in ("FINANCE", "ADMIN"):
        raise PermissionError("A finance account is required")
    row = conn.execute("""SELECT R.*, E.STATUS AS EXPENSE_STATUS FROM REIMBURSEMENTS R
        JOIN EXPENSES E ON R.EXPENSE_ID = E.EXPENSE_ID WHERE R.REIMBURSEMENT_ID = ?""", (reimbursement_id,)).fetchone()
    if row is None:
        raise LookupError("Reimbursement not found")
    if row["STATUS"] != "PENDING" or row["EXPENSE_STATUS"] not in ("MANAGER_APPROVED", "APPROVED"):
        raise ValueError("A manager-approved reimbursement is required")
    _approval(conn, row["EXPENSE_ID"], finance_user_id, "FINANCE", "APPROVED", comments)
    conn.execute("UPDATE REIMBURSEMENTS SET STATUS = 'FINANCE_APPROVED', APPROVED_DATE = date('now') WHERE REIMBURSEMENT_ID = ?", (reimbursement_id,))
    conn.execute("UPDATE EXPENSES SET STATUS = 'FINANCE_APPROVED' WHERE EXPENSE_ID = ?", (row["EXPENSE_ID"],))
    _audit(conn, finance_user_id, "FINANCE_APPROVED", row["EXPENSE_ID"], row["EXPENSE_STATUS"], "FINANCE_APPROVED")
    conn.commit()
    return {"reimbursement_id": reimbursement_id, "expense_id": row["EXPENSE_ID"], "status": "FINANCE_APPROVED"}


def mark_reimbursement_paid(conn, reimbursement_id, finance_user_id, payment_method, transaction_reference):
    user = conn.execute("SELECT ROLE FROM USER WHERE USER_ID = ?", (finance_user_id,)).fetchone()
    if user is None:
        raise LookupError("Finance user not found")
    if user["ROLE"] not in ("FINANCE", "ADMIN"):
        raise PermissionError("A finance account is required")
    method = str(payment_method or "").strip()
    reference = str(transaction_reference or "").strip()
    if not method or not reference:
        raise ValueError("Payment method and transaction reference are required")
    row = conn.execute("SELECT * FROM REIMBURSEMENTS WHERE REIMBURSEMENT_ID = ?", (reimbursement_id,)).fetchone()
    if row is None:
        raise LookupError("Reimbursement not found")
    if row["STATUS"] != "FINANCE_APPROVED":
        raise ValueError("Finance approval is required before payment")
    conn.execute("UPDATE REIMBURSEMENTS SET STATUS = 'PAID', PAID_DATE = date('now'), PAYMENT_METHOD = ?, TRANSACTION_REFERENCE = ? WHERE REIMBURSEMENT_ID = ?", (method, reference, reimbursement_id))
    conn.execute("UPDATE EXPENSES SET STATUS = 'PAID' WHERE EXPENSE_ID = ?", (row["EXPENSE_ID"],))
    _audit(conn, finance_user_id, "REIMBURSEMENT_PAID", row["EXPENSE_ID"], "FINANCE_APPROVED", "PAID")
    conn.commit()
    return {"reimbursement_id": reimbursement_id, "status": "PAID"}


def list_reimbursements(conn, user_id):
    user = conn.execute("SELECT ROLE FROM USER WHERE USER_ID = ?", (user_id,)).fetchone()
    if user is None:
        raise LookupError("User not found")
    if user["ROLE"] not in ("FINANCE", "ADMIN"):
        raise PermissionError("A finance account is required")
    rows = conn.execute("""SELECT R.*, E.DESCRIPTION, E.EXPENSE_DATE, E.STATUS AS EXPENSE_STATUS,
        C.CATEGORY_NAME, P.NAME AS EMPLOYEE_NAME FROM REIMBURSEMENTS R
        JOIN EXPENSES E ON R.EXPENSE_ID = E.EXPENSE_ID
        JOIN EXPENSE_CATEGORIES C ON E.CATEGORY_ID = C.CATEGORY_ID
        JOIN EMPLOYEES P ON R.EMPLOYEE_ID = P.EMPLOYEE_ID
        WHERE R.STATUS IN ('PENDING', 'FINANCE_APPROVED') ORDER BY R.REIMBURSEMENT_ID""").fetchall()
    return [dict(row) for row in rows]


def get_expense_audit(conn, expense_id, user_id):
    user = conn.execute("SELECT ROLE FROM USER WHERE USER_ID = ?", (user_id,)).fetchone()
    if user is None:
        raise LookupError("User not found")
    expense = conn.execute("SELECT EMPLOYEE_ID FROM EXPENSES WHERE EXPENSE_ID = ?", (expense_id,)).fetchone()
    if expense is None:
        raise LookupError("Expense not found")
    if user["ROLE"] == "EMPLOYEE":
        employee = conn.execute("SELECT EMPLOYEE_ID FROM EMPLOYEES WHERE USER_ID = ?", (user_id,)).fetchone()
        if employee is None or employee["EMPLOYEE_ID"] != expense["EMPLOYEE_ID"]:
            raise PermissionError("You can only view your own expense history")
    elif user["ROLE"] not in ("MANAGER", "FINANCE", "ADMIN"):
        raise PermissionError("This account cannot view expense history")
    rows = conn.execute("""SELECT A.ACTION, A.OLD_VALUE, A.NEW_VALUE, A.TIMESTAMP, U.USERNAME
        FROM AUDIT_LOGS A JOIN USER U ON A.USER_ID = U.USER_ID
        WHERE A.ENTITY = 'EXPENSE' AND A.ENTITY_ID = ? ORDER BY A.AUDIT_ID""", (expense_id,)).fetchall()
    return [dict(row) for row in rows]

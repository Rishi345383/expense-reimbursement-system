from datetime import date


def submit_expense(conn, user_id, category_id, expense_date, amount, description, receipt_reference=None):
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
    policy = conn.execute(
        "SELECT MAX_AMOUNT, DAILY_LIMIT, RECEIPT_REQUIRED FROM EXPENSE_POLICIES WHERE CATEGORY_ID = ?",
        (category_id,)
    ).fetchone()
    if policy is None:
        raise LookupError("Expense category or policy not found")
    if policy["RECEIPT_REQUIRED"] and not receipt_reference:
        raise ValueError("A receipt reference is required for this category")

    daily_total = conn.execute(
        "SELECT COALESCE(SUM(AMOUNT), 0) FROM EXPENSES WHERE EMPLOYEE_ID = ? AND EXPENSE_DATE = ? AND STATUS != 'REJECTED'",
        (employee["EMPLOYEE_ID"], expense_date)
    ).fetchone()[0]
    policy_status = "NON_COMPLIANT" if amount > policy["MAX_AMOUNT"] or daily_total + amount > policy["DAILY_LIMIT"] else "COMPLIANT"
    cursor = conn.execute(
        """INSERT INTO EXPENSES (EMPLOYEE_ID, CATEGORY_ID, EXPENSE_DATE, SUBMITTED_AT, AMOUNT,
           DESCRIPTION, RECEIPT_REFERENCE, POLICY_STATUS, RISK_SCORE, STATUS)
           VALUES (?, ?, ?, datetime('now'), ?, ?, ?, ?, 0, 'PENDING')""",
        (employee["EMPLOYEE_ID"], category_id, expense_date, amount, description, receipt_reference, policy_status)
    )
    conn.commit()
    return cursor.lastrowid


def list_expenses(conn, user_id):
    user = conn.execute("SELECT ROLE FROM USER WHERE USER_ID = ?", (user_id,)).fetchone()
    if user is None:
        raise LookupError("User not found")
    if user["ROLE"] == "EMPLOYEE":
        employee = conn.execute("SELECT EMPLOYEE_ID FROM EMPLOYEES WHERE USER_ID = ?", (user_id,)).fetchone()
        if employee is None:
            raise LookupError("Employee profile not found")
        rows = conn.execute(
            """SELECT E.*, C.CATEGORY_NAME FROM EXPENSES E
               JOIN EXPENSE_CATEGORIES C ON E.CATEGORY_ID = C.CATEGORY_ID
               WHERE E.EMPLOYEE_ID = ? ORDER BY E.EXPENSE_ID DESC""",
            (employee["EMPLOYEE_ID"],)
        ).fetchall()
    elif user["ROLE"] in ("MANAGER", "FINANCE", "ADMIN"):
        rows = conn.execute(
            """SELECT E.*, C.CATEGORY_NAME FROM EXPENSES E
               JOIN EXPENSE_CATEGORIES C ON E.CATEGORY_ID = C.CATEGORY_ID
               ORDER BY E.EXPENSE_ID DESC"""
        ).fetchall()
    else:
        raise PermissionError("This account cannot view expenses")
    return [dict(row) for row in rows]


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
    if expense["STATUS"] != "PENDING":
        raise ValueError("Only pending expenses can be reviewed")

    approval_id = conn.execute("SELECT COALESCE(MAX(APPROVAL_ID), 0) + 1 FROM APPROVALS").fetchone()[0]
    conn.execute(
        """INSERT INTO APPROVALS (APPROVAL_ID, EXPENSE_ID, APPROVER_ID, APPROVAL_LEVEL, DECISION, COMMENTS, APPROVAL_DATE)
           VALUES (?, ?, ?, 'MANAGER', ?, ?, datetime('now'))""",
        (approval_id, expense_id, approver_id, decision, str(comments or ""))
    )
    conn.execute("UPDATE EXPENSES SET STATUS = ? WHERE EXPENSE_ID = ?", (decision, expense_id))
    reimbursement_id = None
    if decision == "APPROVED":
        cursor = conn.execute(
            """INSERT INTO REIMBURSEMENTS (EXPENSE_ID, EMPLOYEE_ID, CLAIMED_AMOUNT, APPROVED_AMOUNT,
               REQUESTED_DATE, APPROVED_DATE, STATUS)
               VALUES (?, ?, ?, ?, date('now'), date('now'), 'PENDING')""",
            (expense_id, expense["EMPLOYEE_ID"], expense["AMOUNT"], expense["AMOUNT"])
        )
        reimbursement_id = cursor.lastrowid
    conn.commit()
    return {"expense_id": expense_id, "status": decision, "reimbursement_id": reimbursement_id}


def mark_reimbursement_paid(conn, reimbursement_id, finance_user_id, payment_method, transaction_reference):
    user = conn.execute("SELECT ROLE FROM USER WHERE USER_ID = ?", (finance_user_id,)).fetchone()
    if user is None:
        raise LookupError("Finance user not found")
    if user["ROLE"] not in ("FINANCE", "ADMIN"):
        raise PermissionError("A finance account is required")
    payment_method = str(payment_method or "").strip()
    transaction_reference = str(transaction_reference or "").strip()
    if not payment_method or not transaction_reference:
        raise ValueError("Payment method and transaction reference are required")
    reimbursement = conn.execute(
        "SELECT STATUS FROM REIMBURSEMENTS WHERE REIMBURSEMENT_ID = ?", (reimbursement_id,)
    ).fetchone()
    if reimbursement is None:
        raise LookupError("Reimbursement not found")
    if reimbursement["STATUS"] != "PENDING":
        raise ValueError("Only pending reimbursements can be marked paid")
    conn.execute(
        """UPDATE REIMBURSEMENTS SET STATUS = 'PAID', PAID_DATE = date('now'),
           PAYMENT_METHOD = ?, TRANSACTION_REFERENCE = ? WHERE REIMBURSEMENT_ID = ?""",
        (payment_method, transaction_reference, reimbursement_id)
    )
    conn.commit()
    return {"reimbursement_id": reimbursement_id, "status": "PAID"}


def list_reimbursements(conn, user_id):
    user = conn.execute("SELECT ROLE FROM USER WHERE USER_ID = ?", (user_id,)).fetchone()
    if user is None:
        raise LookupError("User not found")
    if user["ROLE"] not in ("FINANCE", "ADMIN"):
        raise PermissionError("A finance account is required")
    rows = conn.execute(
        """SELECT R.*, E.DESCRIPTION, E.EXPENSE_DATE, C.CATEGORY_NAME, P.NAME AS EMPLOYEE_NAME
           FROM REIMBURSEMENTS R
           JOIN EXPENSES E ON R.EXPENSE_ID = E.EXPENSE_ID
           JOIN EXPENSE_CATEGORIES C ON E.CATEGORY_ID = C.CATEGORY_ID
           JOIN EMPLOYEES P ON R.EMPLOYEE_ID = P.EMPLOYEE_ID
           WHERE R.STATUS = 'PENDING' ORDER BY R.REIMBURSEMENT_ID"""
    ).fetchall()
    return [dict(row) for row in rows]

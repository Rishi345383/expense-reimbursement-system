
from app.services.user_service import get_user_by_username
from app.services.user_service import (
    get_user_by_id,
    get_user_by_username,
    create_user
)
from fastapi import FastAPI, HTTPException

from app.database import get_db
from app.services.user_service import get_user_by_id

app = FastAPI(
    title="Expense & Reimbursement Management System"
)


@app.get("/")
def home():
    return FileResponse(str(Path(__file__).resolve().parent.parent / "static" / "index.html"))


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/users/{user_id}")
def read_user(user_id: int):
    conn = get_db()

    try:
        user = get_user_by_id(conn, user_id)

        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        return {
            "user_id": user["USER_ID"],
            "username": user["USERNAME"],
            "role": user["ROLE"],
            "status": user["STATUS"],
            "created_at": user["CREATED_AT"]
        }

    finally:
        conn.close()
@app.post("/auth/register")
def register_user(
    username: str,
    password: str
):
    conn = get_db()

    try:
        existing_user = get_user_by_username(conn, username)

        if existing_user is not None:
            raise HTTPException(
                status_code=409,
                detail="Username already exists"
            )

        user_id = create_user(
            conn,
            username,
            password,
            "EMPLOYEE",
            "ACTIVE"
        )

        return {
            "message": "User registered successfully",
            "user_id": user_id,
            "username": username,
            "role": "EMPLOYEE"
        }

    finally:
        conn.close()
@app.post("/auth/login")
def login_user(
    username: str,
    password: str
):

    conn = get_db()

    try:
        user = get_user_by_username(conn, username)

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )

        if user["PASSWORD"] != password:
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )

        if user["STATUS"] != "ACTIVE":
            raise HTTPException(
                status_code=403,
                detail="User account is not active"
            )

        return {
            "message": "Login successful",
            "user_id": user["USER_ID"],
            "username": user["USERNAME"],
            "role": user["ROLE"]
        }

    finally:
        conn.close()

from fastapi import Request
from app.services.expense_service import (
    submit_expense, list_expenses, review_expense, mark_reimbursement_paid
)


def workflow_error(error):
    if isinstance(error, LookupError):
        raise HTTPException(status_code=404, detail=str(error))
    if isinstance(error, PermissionError):
        raise HTTPException(status_code=403, detail=str(error))
    if isinstance(error, ValueError):
        raise HTTPException(status_code=400, detail=str(error))
    raise error


@app.post("/expenses")
async def create_expense_route(request: Request):
    data = await request.json()
    conn = get_db()
    try:
        expense_id = submit_expense(
            conn, data.get("user_id"), data.get("category_id"), data.get("expense_date"),
            data.get("amount"), data.get("description"), data.get("receipt_reference")
        )
        return {"message": "Expense submitted", "expense_id": expense_id, "status": "PENDING"}
    except (LookupError, PermissionError, ValueError) as error:
        workflow_error(error)
    finally:
        conn.close()


@app.get("/expenses")
def get_expenses(user_id: int):
    conn = get_db()
    try:
        return list_expenses(conn, user_id)
    except (LookupError, PermissionError, ValueError) as error:
        workflow_error(error)
    finally:
        conn.close()


@app.post("/expenses/{expense_id}/review")
async def review_expense_route(expense_id: int, request: Request):
    data = await request.json()
    conn = get_db()
    try:
        return review_expense(
            conn, expense_id, data.get("approver_id"), data.get("decision"), data.get("comments", "")
        )
    except (LookupError, PermissionError, ValueError) as error:
        workflow_error(error)
    finally:
        conn.close()


@app.post("/reimbursements/{reimbursement_id}/paid")
async def mark_paid_route(reimbursement_id: int, request: Request):
    data = await request.json()
    conn = get_db()
    try:
        return mark_reimbursement_paid(
            conn, reimbursement_id, data.get("finance_user_id"),
            data.get("payment_method"), data.get("transaction_reference")
        )
    except (LookupError, PermissionError, ValueError) as error:
        workflow_error(error)
    finally:
        conn.close()

from pathlib import Path
from fastapi.responses import FileResponse
from app.services.expense_service import list_reimbursements


@app.get("/categories")
def get_categories():
    conn = get_db()
    try:
        return [dict(row) for row in conn.execute(
            "SELECT CATEGORY_ID, CATEGORY_NAME FROM EXPENSE_CATEGORIES ORDER BY CATEGORY_NAME"
        ).fetchall()]
    finally:
        conn.close()


@app.get("/reimbursements")
def get_reimbursements(user_id: int):
    conn = get_db()
    try:
        return list_reimbursements(conn, user_id)
    except (LookupError, PermissionError, ValueError) as error:
        workflow_error(error)
    finally:
        conn.close()

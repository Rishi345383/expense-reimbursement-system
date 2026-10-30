
from app.database import get_db
from app.services.user_service import (
    get_user_by_id,
    get_user_by_username,
    create_user,
)

conn = get_db()

try:
    username = "testuser"

    # Check whether the test user already exists
    user = get_user_by_username(conn, username)

    if user is None:
        user_id = create_user(
            conn,
            username,
            "TestPassword123",
            "EMPLOYEE",
            "ACTIVE"
        )
        print("User created successfully. ID:", user_id)
    else:
        print("Test user already exists. ID:", user["USER_ID"])

    # Verify the user can be retrieved
    user = get_user_by_username(conn, username)
    print("Retrieved user:", user["USERNAME"] if user else None)

finally:
    conn.close()

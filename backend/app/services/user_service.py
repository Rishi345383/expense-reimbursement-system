def get_user_by_id(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM USER WHERE USER_ID = ?", (user_id,))
    user = cursor.fetchone()
    return user

def get_user_by_id(conn, user_id):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM USER WHERE USER_ID = ?",
        (user_id,)
    )
    user = cursor.fetchone()
    return user
def get_user_by_username(conn, username):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM USER WHERE USERNAME = ?",
        (username,)
    )
    user = cursor.fetchone()
    return user


def create_user(conn, username, password, role, status):
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO USER (
            USER_ID,
            USERNAME,
            PASSWORD,
            ROLE,
            STATUS,
            CREATED_AT
        )
        VALUES (
            (SELECT COALESCE(MAX(USER_ID), 0) + 1 FROM USER),
            ?, ?, ?, ?, datetime('now')
        )
        """,
        (username, password, role, status)
    )

    conn.commit()

    return cursor.lastrowid

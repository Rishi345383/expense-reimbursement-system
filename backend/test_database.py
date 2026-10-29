from app.services.user_service import get_user_by_id
from app.database import get_db
conn=get_db()
try:
    user = get_user_by_id(conn, 1)
    print(user)
    cursor=conn.cursor()
    cursor.execute("SELECT * FROM USER")
    users=cursor.fetchall()
    for i in users:
        print(i["USERNAME"])
    print("Database test successful!")
finally:
    conn.close()
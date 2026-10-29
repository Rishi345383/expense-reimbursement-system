import sqlite3
db="smart_expenses1.db"
conn=sqlite3.connect(db)
print("samrt db created")
conn.execute("PRAGMA foreign_keys=ON;")
conn.execute('''CREATE TABLE USER
             (USER_ID INT PRIMARY KEY,
              USERNAME TEXT NOT NULL,
              PASSWORD TEXT NOT NULL,
              ROLE TEXT NOT NULL,
              STATUS TEXT NOT NULL,
              CREATED_AT TEXT NOT NULL);''')
print("  USER DETAILS  ")
def user_details():
    USER_ID1=int(input("Enter the user id"))
    USERNAME1=input("Enter the username")
    PASSWORD1=input("Enter the password")
    ROLE1=input("Enter the role")
    STATUS1=input("Enter the status")
    CREATED_AT1=input("Enter the date of creation")
    cursor=conn.cursor()
    cursor.execute(
        '''INSERT INTO USER
        (USER_ID,USERNAME,PASSWORD,ROLE,STATUS,CREATED_AT)
        VALUES(?,?,?,?,?,?)''',
        (USER_ID1,USERNAME1,PASSWORD1,ROLE1,STATUS1,CREATED_AT1)
    )
    conn.commit()
    print("user details inserted sucessfully")

def view_all1():
    cursor=conn.cursor()
    cursor.execute("SELECT*FROM USER")
    rows=cursor.fetchall()
    for row in rows:
        print(f"USER_ID1:{row[0]}|USERNAME1:{row[1]}|PASSWORD1:{row[2]}|ROLE1:{row[3]}|STATUS1:{row[4]}|CREATED_AT:{row[5]}")
        print()
view_all1()
conn.execute('''CREATE TABLE EMPLOYEES
              (EMPLOYEE_ID INTEGER PRIMARY KEY,
              USER_ID INTEGER NOT NULL,
              NAME TEXT NOT NULL,
              EMAIL TEXT NOT NULL UNIQUE,
              PHONE TEXT NOT NULL,
              DEPARTMENT TEXT NOT NULL,
              MANAGER_ID INTEGER,
              FOREIGN KEY (USER_ID) REFERENCES USER(USER_ID),
              FOREIGN KEY (MANAGER_ID) REFERENCES USER(USER_ID));''')

print("EMPLOYEES table created")
print("  EMPLOYEE DETAILS  ")
def employee_details():
    EMPLOYEE_ID1=int(input("Enter the employee id"))
    USER_ID1=int(input("Enter the user id"))
    NAME1=input("Enter the employee name")
    EMAIL1=input("Enter the employee mail")
    PHONE1=input("Enter the phone number of employee")
    DEPARTMENT1=input("Enter the employee department")
    MANAGER_ID1=int(input("Enter the manager id"))
    cursor=conn.cursor()
    cursor.execute(
        '''INSERT INTO EMPLOYEES
        (EMPLOYEE_ID,USER_ID,NAME,EMAIL,PHONE,DEPARTMENT,MANAGER_ID)
        VALUES(?,?,?,?,?,?,?)''',
        (EMPLOYEE_ID1,USER_ID1,NAME1,EMAIL1,PHONE1,DEPARTMENT1,MANAGER_ID1)
    )
    conn.commit()
    print("Employee details entered sucesfully")

def view_all2():
    cursor=conn.cursor()
    cursor.execute("SELECT*FROM EMPLOYEES")
    rows=cursor.fetchall()
    for row in rows:
        print(f"EMPLOYEE_ID1:{row[0]}|USER_ID1:{row[1]}|NAME1:{row[2]}|EMAIL1:{row[3]}|PHONE1:{row[4]}|DEPARTMENT1:{row[5]}|MANAGER_ID1:{row[6]}")
        print()
view_all2()
conn.execute('''CREATE TABLE EXPENSE_CATEGORIES
              (CATEGORY_ID INTEGER PRIMARY KEY,
              CATEGORY_NAME TEXT NOT NULL UNIQUE);''')

print("EXPENSE_CATEGORIES table created")
print("   EXPENSE_CATEGORIES  ")
def expense_cat():
    CATEGORY_ID1=int(input("Enter the Category id"))
    CATEGORY_NAME1=input("enter the category name")
    cursor=conn.cursor()
    cursor.execute(
        '''INSERT INTO EXPENSE_CATEGORIES
        (CATEGORY_ID,CATEGORY_NAME)
        VALUES(?,?)''',
        (CATEGORY_ID1,CATEGORY_NAME1)
    )
    conn.commit()
    print("Category details entered sucessfully")

def view_all3():
    cursor=conn.cursor()
    cursor.execute("SELECT*FROM EXPENSE_CATEGORIES")
    rows=cursor.fetchall()
    for row in rows:
        print(f"CATEGORY_ID1:{row[0]}|CATEGORY_NAME1:{row[1]}")
        print()
view_all3()
conn.execute('''CREATE TABLE EXPENSE_POLICIES
              (POLICY_ID INTEGER PRIMARY KEY,
              CATEGORY_ID INTEGER NOT NULL,
              MAX_AMOUNT REAL NOT NULL,
              DAILY_LIMIT REAL NOT NULL,
              RECEIPT_REQUIRED INTEGER NOT NULL,
              MANAGER_APPROVAL_REQUIRED INTEGER NOT NULL,
              FINANCE_APPROVAL_REQUIRED INTEGER NOT NULL,
              FOREIGN KEY (CATEGORY_ID)
              REFERENCES EXPENSE_CATEGORIES(CATEGORY_ID));''')

print("EXPENSE_POLICIES table created")
print("  EXPENSE_POLICIES  ")
def expense_policies():
    POLICY_ID1 = int(input("Enter the policy id: "))
    CATEGORY_ID1 = int(input("Enter the category id: "))
    MAX_AMOUNT1 = float(input("Enter the max amount: "))
    DAILY_LIMIT1 = float(input("Enter the daily limit: "))
    RECEIPT_REQUIRED1 = int(input("Receipt required? Enter 1 for Yes, 0 for No: "))
    MANAGER_APPROVAL_REQUIRED1 = int(input("Manager approval required? Enter 1 for Yes, 0 for No: "))
    FINANCE_APPROVAL_REQUIRED1 = int(input("Finance approval required? Enter 1 for Yes, 0 for No: "))
    cursor=conn.cursor()
    cursor.execute(
        '''INSERT INTO EXPENSE_POLICIES
        (POLICY_ID,CATEGORY_ID,MAX_AMOUNT,DAILY_LIMIT,RECEIPT_REQUIRED,MANAGER_APPROVAL_REQUIRED,FINANCE_APPROVAL_REQUIRED)
        VALUES(?,?,?,?,?,?,?)''',
        (POLICY_ID1,CATEGORY_ID1,MAX_AMOUNT1,DAILY_LIMIT1,RECEIPT_REQUIRED1,MANAGER_APPROVAL_REQUIRED1,FINANCE_APPROVAL_REQUIRED1)
    )
    conn.commit()
    print("EXPENSE_POLICIES entered sucessfully")

def view_all4():
    cursor=conn.cursor()
    cursor.execute("SELECT*FROM EXPENSE_POLICIES")
    rows=cursor.fetchall()
    for row in rows:
        print(f"POLICY_ID1:{row[0]}|CATEGORY_ID{row[1]}|MAX_AMOUNT1:{row[2]}|DAILY_LIMIT1:{row[3]}|RECEIPT_REQUIRED1:{row[4]}|MANAGER_APPROVAL_REQUIRED1:{row[5]}|FINANCE_APPROVAL_REQUIRED1:{row[6]}")
        print()
view_all4()
conn.execute('''CREATE TABLE EXPENSES
              (EXPENSE_ID INTEGER PRIMARY KEY,
              EMPLOYEE_ID INTEGER NOT NULL,
              CATEGORY_ID INTEGER NOT NULL,
              EXPENSE_DATE TEXT NOT NULL,
              SUBMITTED_AT TEXT NOT NULL,
              AMOUNT REAL NOT NULL,
              DESCRIPTION TEXT NOT NULL,
              RECEIPT_REFERENCE TEXT,
              POLICY_STATUS TEXT NOT NULL,
              RISK_SCORE INTEGER NOT NULL,
              STATUS TEXT NOT NULL,
              FOREIGN KEY (EMPLOYEE_ID)
              REFERENCES EMPLOYEES(EMPLOYEE_ID),
              FOREIGN KEY (CATEGORY_ID)
              REFERENCES EXPENSE_CATEGORIES(CATEGORY_ID));''')

print("EXPENSES table created")
def expenses():
    EXPENSE_ID1=int(input("Enter the expense id:"))
    EMPLOYEE_ID1=int(input("Enter the employee id:"))
    CATEGORY_ID1=int(input("Enter the category id:"))
    EXPENSE_DATE1=input("Enter the expense date:")
    SUBMITTED_AT1=input("Enter the date of submission:")
    AMOUNT1=float(input("Enter the amount:"))
    DESCRIPTION1=input("Enter the purpose:")
    RECEIPT_REFERENCE1=input("Enter the Receipt reference: ")
    POLICY_STATUS1=input("Policy status:")
    RISK_SCORE1=int(input("Risk Score is:"))
    STATUS1=input("Status:")
    cursor=conn.cursor()
    cursor.execute(
        '''INSERT INTO EXPENSES
        (EXPENSE_ID,EMPLOYEE_ID,CATEGORY_ID,EXPENSE_DATE,SUBMITTED_AT,AMOUNT,DESCRIPTION,RECEIPT_REFERENCE,POLICY_STATUS,RISK_SCORE,STATUS)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)''',
        (EXPENSE_ID1,EMPLOYEE_ID1,CATEGORY_ID1,EXPENSE_DATE1,SUBMITTED_AT1,AMOUNT1,DESCRIPTION1,RECEIPT_REFERENCE1,POLICY_STATUS1,RISK_SCORE1,STATUS1)
    )
    conn.commit()
    print("EXPENSES entered sucessfully")

def view_all5():
    cursor=conn.cursor()
    cursor.execute("SELECT*FROM EXPENSES")
    rows=cursor.fetchall()
    for row in rows:
        print(f"EXPENSE_ID1:{row[0]}|EMPLOYEE_ID1:{row[1]}|CATEGORY_ID1:{row[2]}|EXPENSE_DATE1:{row[3]}|SUBMITTED_AT1:{row[4]}|AMOUNT1:{row[5]}|DESCRIPTION1:{row[6]}|RECEIPT_REFERENCE1:{row[7]}|POLICY_STATUS1:{row[8]}|RISK_SCORE1:{row[9]}|STATUS1:{row[10]}|")
        print()
view_all5()
conn.execute(''' CREATE TABLE APPROVALS
              (APPROVAL_ID INT PRIMARY KEY,
              EXPENSE_ID INT NOT NULL,
              APPROVER_ID INT NOT NULL,
              APPROVAL_LEVEL TEXT NOT NULL,
              DECISION TEXT NOT NULL,
              COMMENTS TEXT NOT NULL,
              APPROVAL_DATE TEXT NOT NULL);''')
print("  APPROVALS  ")
def approvals():
    APPROVAL_ID1=int(input("Enter the approval id:"))
    EXPENSE_ID1=int(input("Enter the expense id:"))
    APPROVER_ID1=int(input("Enter the approver id:"))
    APPROVAL_LEVEL1=input("Enter the approval level:")
    DECISION1=input("DECISION:")
    COMMENTS1=input("Enter comments if any")
    APPROVAL_DATE1=input("Date of approval:")
    cursor=conn.cursor()
    cursor.execute(
        '''INSERT INTO APPROVALS
        (APPROVAL_ID,EXPENSE_ID,APPROVER_ID,APPROVAL_LEVEL,DECISION,COMMENTS,APPROVAL_DATE)
        VALUES(?,?,?,?,?,?,?)''',
        (APPROVAL_ID1,EXPENSE_ID1,APPROVER_ID1,APPROVAL_LEVEL1,DECISION1,COMMENTS1,APPROVAL_DATE1)
    )
    conn.commit()
    print("APPROVALS entered sucessfully")

def view_all6():
    cursor=conn.cursor()
    cursor.execute("SELECT*FROM APPROVALS")
    rows=cursor.fetchall()
    for row in rows:
        print(f"APPROVAL_ID1:{row[0]}|EXPENSE_ID1{row[1]}|APPROVER_ID1:{row[2]}|APPROVAL_LEVEL1:{row[3]}|DECISION1:{row[4]}|COMMENTS1:{row[5]}|APPROVAL_DATE1:{row[6]}")
        print()
view_all6()
conn.execute('''CREATE TABLE RISK_FLAGS
              (RISK_ID INTEGER PRIMARY KEY,
              EXPENSE_ID INTEGER NOT NULL,
              RISK_TYPE TEXT NOT NULL,
              SEVERITY TEXT NOT NULL,
              REASON TEXT NOT NULL,
              CREATED_AT TEXT NOT NULL,
              RESOLUTION_STATUS TEXT NOT NULL,
              FOREIGN KEY (EXPENSE_ID)
              REFERENCES EXPENSES(EXPENSE_ID));''')

print("RISK_FLAGS table created")

print("RISK_FLAGS")
def risk_flags():
    RISK_ID1 = int(input("Enter the risk id: "))
    EXPENSE_ID1 = int(input("Enter the expense id: "))
    RISK_TYPE1 = input("Enter the risk type: ")
    SEVERITY1 = input("Enter the severity: ")
    REASON1 = input("Enter the reason: ")
    CREATED_AT1 = input("Enter created date and time: ")
    RESOLUTION_STATUS1 = input("Enter resolution status: ")

    cursor = conn.cursor()

    cursor.execute(
        '''INSERT INTO RISK_FLAGS
        (RISK_ID, EXPENSE_ID, RISK_TYPE, SEVERITY,
         REASON, CREATED_AT, RESOLUTION_STATUS)
        VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (RISK_ID1, EXPENSE_ID1, RISK_TYPE1, SEVERITY1,
         REASON1, CREATED_AT1, RESOLUTION_STATUS1)
    )

    conn.commit()
    print("RISK FLAG entered successfully")

def view_all7():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM RISK_FLAGS")
    rows = cursor.fetchall()

    for row in rows:
        print(f"RISK_ID: {row[0]} |EXPENSE_ID: {row[1]} |RISK_TYPE: {row[2]} |SEVERITY: {row[3]} |REASON: {row[4]} |CREATED_AT: {row[5]} |RESOLUTION_STATUS: {row[6]}")
        print()
view_all7()
conn.execute('''CREATE TABLE REIMBURSEMENTS
              (REIMBURSEMENT_ID INTEGER PRIMARY KEY,
              EXPENSE_ID INTEGER NOT NULL,
              EMPLOYEE_ID INTEGER NOT NULL,
              CLAIMED_AMOUNT REAL NOT NULL,
              APPROVED_AMOUNT REAL NOT NULL,
              REQUESTED_DATE TEXT NOT NULL,
              APPROVED_DATE TEXT,
              PAID_DATE TEXT,
              STATUS TEXT NOT NULL,
              PAYMENT_METHOD TEXT,
              TRANSACTION_REFERENCE TEXT,
              FOREIGN KEY (EXPENSE_ID)
              REFERENCES EXPENSES(EXPENSE_ID),
              FOREIGN KEY (EMPLOYEE_ID)
              REFERENCES EMPLOYEES(EMPLOYEE_ID));''')

print("REIMBURSEMENTS table created")

print("REIMBURSEMENTS")
def reimbursements():
    REIMBURSEMENT_ID1 = int(input("Enter the reimbursement id: "))
    EXPENSE_ID1 = int(input("Enter the expense id: "))
    EMPLOYEE_ID1 = int(input("Enter the employee id: "))
    CLAIMED_AMOUNT1 = float(input("Enter the claimed amount: "))
    APPROVED_AMOUNT1 = float(input("Enter the approved amount: "))
    REQUESTED_DATE1 = input("Enter requested date: ")
    APPROVED_DATE1 = input("Enter approved date: ")
    PAID_DATE1 = input("Enter paid date: ")
    STATUS1 = input("Enter reimbursement status: ")
    PAYMENT_METHOD1 = input("Enter payment method: ")
    TRANSACTION_REFERENCE1 = input("Enter transaction reference: ")

    cursor = conn.cursor()

    cursor.execute(
        '''INSERT INTO REIMBURSEMENTS
        (REIMBURSEMENT_ID, EXPENSE_ID, EMPLOYEE_ID,
         CLAIMED_AMOUNT, APPROVED_AMOUNT, REQUESTED_DATE,
         APPROVED_DATE, PAID_DATE, STATUS,
         PAYMENT_METHOD, TRANSACTION_REFERENCE)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (REIMBURSEMENT_ID1, EXPENSE_ID1, EMPLOYEE_ID1,
         CLAIMED_AMOUNT1, APPROVED_AMOUNT1, REQUESTED_DATE1,
         APPROVED_DATE1, PAID_DATE1, STATUS1,
         PAYMENT_METHOD1, TRANSACTION_REFERENCE1)
    )

    conn.commit()
    print("REIMBURSEMENT entered successfully")

def view_all8():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM REIMBURSEMENTS")
    rows = cursor.fetchall()

    for row in rows:
        print(f"REIMBURSEMENT_ID: {row[0]} |EXPENSE_ID: {row[1]} |EMPLOYEE_ID: {row[2]} |CLAIMED_AMOUNT: {row[3]} |APPROVED_AMOUNT: {row[4]} |REQUESTED_DATE: {row[5]} |APPROVED_DATE: {row[6]} |PAID_DATE: {row[7]} |STATUS: {row[8]} |PAYMENT_METHOD: {row[9]} |TRANSACTION_REFERENCE: {row[10]}")
        print()
view_all8()
conn.execute('''CREATE TABLE AUDIT_LOGS
              (AUDIT_ID INTEGER PRIMARY KEY,
              USER_ID INTEGER NOT NULL,
              ACTION TEXT NOT NULL,
              ENTITY TEXT NOT NULL,
              ENTITY_ID INTEGER NOT NULL,
              OLD_VALUE TEXT,
              NEW_VALUE TEXT,
              TIMESTAMP TEXT NOT NULL,
              FOREIGN KEY (USER_ID)
              REFERENCES USER(USER_ID));''')

print("AUDIT_LOGS table created")

print("AUDIT_LOGS")
def audit_logs():
    AUDIT_ID1 = int(input("Enter the audit id: "))
    USER_ID1 = int(input("Enter the user id: "))
    ACTION1 = input("Enter action: ")
    ENTITY1 = input("Enter entity: ")
    ENTITY_ID1 = int(input("Enter entity id: "))
    OLD_VALUE1 = input("Enter old value: ")
    NEW_VALUE1 = input("Enter new value: ")
    TIMESTAMP1 = input("Enter timestamp: ")

    cursor = conn.cursor()

    cursor.execute(
        '''INSERT INTO AUDIT_LOGS
        (AUDIT_ID, USER_ID, ACTION, ENTITY,
         ENTITY_ID, OLD_VALUE, NEW_VALUE, TIMESTAMP)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (AUDIT_ID1, USER_ID1, ACTION1, ENTITY1,
         ENTITY_ID1, OLD_VALUE1, NEW_VALUE1, TIMESTAMP1)
    )

    conn.commit()
    print("AUDIT LOG entered successfully")

def view_all9():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM AUDIT_LOGS")
    rows = cursor.fetchall()

    for row in rows:
        print(f"AUDIT_ID: {row[0]} |USER_ID: {row[1]} |ACTION: {row[2]} | ENTITY: {row[3]} | ENTITY_ID: {row[4]} |OLD_VALUE: {row[5]} |NEW_VALUE: {row[6]} |TIMESTAMP: {row[7]}")
        print()
view_all9()

import json
import os
import shutil
import socket
import sqlite3
import tempfile
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import app.database as database
from app.main import app
import uvicorn


def add_user(conn, user_id, username, role):
    conn.execute(
        "INSERT INTO USER (USER_ID, USERNAME, PASSWORD, ROLE, STATUS, CREATED_AT) VALUES (?, ?, ?, ?, 'ACTIVE', datetime('now'))",
        (user_id, username, 'temporary-test-password', role)
    )


def request_json(url, method='GET', payload=None):
    data = None if payload is None else json.dumps(payload).encode('utf-8')
    request = Request(url, data=data, method=method, headers={'Content-Type': 'application/json'})
    try:
        with urlopen(request, timeout=5) as response:
            body = response.read().decode('utf-8')
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                pass
            return response.status, body
    except HTTPError as error:
        return error.code, json.loads(error.read().decode('utf-8'))


def main():
    handle, temp_path = tempfile.mkstemp(suffix='.db')
    os.close(handle)
    original_database = database.DATABASE_NAME
    server = None
    thread = None
    listener = socket.socket()
    try:
        shutil.copy2(original_database, temp_path)
        database.DATABASE_NAME = temp_path
        conn = sqlite3.connect(temp_path)
        manager_id = conn.execute('SELECT COALESCE(MAX(USER_ID), 0) + 1 FROM USER').fetchone()[0]
        finance_id = manager_id + 1
        add_user(conn, manager_id, 'api_test_manager', 'MANAGER')
        add_user(conn, finance_id, 'api_test_finance', 'FINANCE')
        conn.commit()
        conn.close()

        listener.bind(('127.0.0.1', 0))
        listener.listen(5)
        port = listener.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(app, log_level='error'))
        server.install_signal_handlers = lambda: None
        thread = threading.Thread(target=server.run, kwargs={'sockets': [listener]}, daemon=True)
        thread.start()
        for _ in range(50):
            if server.started:
                break
            time.sleep(0.1)
        if not server.started:
            raise RuntimeError('API server did not start')
        base = 'http://127.0.0.1:' + str(port)

        status, page = request_json(base + '/')
        assert status == 200 and 'Expense & Reimbursement' in page, page
        print('GET / browser page: PASS')
        status, categories = request_json(base + '/categories')
        assert status == 200 and any(item['CATEGORY_NAME'] == 'Travel' for item in categories), categories
        print('GET /categories: PASS')

        status, result = request_json(base + '/expenses', 'POST', {
            'user_id': 2, 'category_id': 1, 'expense_date': '2026-10-30',
            'amount': 450, 'description': 'API workflow test', 'receipt_reference': 'API-RECEIPT'
        })
        assert status == 200, result
        expense_id = result['expense_id']
        print('POST /expenses: PASS')
        assert 'password' not in json.dumps(result).lower()

        status, rows = request_json(base + '/expenses?user_id=2')
        assert status == 200 and any(row['EXPENSE_ID'] == expense_id for row in rows), rows
        print('GET /expenses: PASS')

        status, result = request_json(base + '/expenses/' + str(expense_id) + '/review', 'POST', {
            'approver_id': manager_id, 'decision': 'APPROVED', 'comments': 'Terminal API test'
        })
        assert status == 200, result
        reimbursement_id = result['reimbursement_id']
        print('POST manager review: PASS')
        status, rows = request_json(base + '/reimbursements?user_id=' + str(finance_id))
        assert status == 200 and any(row['REIMBURSEMENT_ID'] == reimbursement_id for row in rows), rows
        print('GET /reimbursements: PASS')

        status, result = request_json(base + '/reimbursements/' + str(reimbursement_id) + '/paid', 'POST', {
            'finance_user_id': finance_id, 'payment_method': 'Bank transfer', 'transaction_reference': 'API-TEST-001'
        })
        assert status == 200 and result['status'] == 'PAID', result
        print('POST finance payment: PASS')
        print('FastAPI end-to-end check: PASS')
    finally:
        if server is not None:
            server.should_exit = True
        if thread is not None:
            thread.join(timeout=5)
        listener.close()
        database.DATABASE_NAME = original_database
        if os.path.exists(temp_path):
            os.remove(temp_path)


if __name__ == '__main__':
    main()

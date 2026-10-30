import asyncio
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
from app.services.expense_service import approve_reimbursement, create_expense_draft, get_expense_audit, list_expenses, mark_reimbursement_paid, review_expense, submit_draft
import uvicorn


def add_user(conn, user_id, username, role):
    conn.execute("INSERT INTO USER (USER_ID, USERNAME, PASSWORD, ROLE, STATUS, CREATED_AT) VALUES (?, ?, ?, ?, 'ACTIVE', datetime('now'))", (user_id, username, 'temporary-test-password', role))


def request_json(url, method='GET', payload=None):
    data = None if payload is None else json.dumps(payload).encode('utf-8')
    request = Request(url, data=data, method=method, headers={'Content-Type': 'application/json'})
    try:
        with urlopen(request, timeout=5) as response:
            body = response.read().decode('utf-8')
            try: body = json.loads(body)
            except json.JSONDecodeError: pass
            return response.status, body
    except HTTPError as error:
        return error.code, json.loads(error.read().decode('utf-8'))


def main():
    handle, path = tempfile.mkstemp(suffix='.db')
    os.close(handle)
    original = database.DATABASE_NAME
    listener = socket.socket()
    server = None
    thread = None
    try:
        shutil.copy2(original, path)
        database.DATABASE_NAME = path
        conn = sqlite3.connect(path)
        manager_id = conn.execute('SELECT COALESCE(MAX(USER_ID), 0) + 1 FROM USER').fetchone()[0]
        finance_id = manager_id + 1
        add_user(conn, manager_id, 'workflow_manager', 'MANAGER')
        add_user(conn, finance_id, 'workflow_finance', 'FINANCE')
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
            if server.started: break
            time.sleep(0.1)
        assert server.started, 'API server did not start'
        base = 'http://127.0.0.1:' + str(port)

        status, page = request_json(base + '/')
        assert status == 200 and 'DRAFT' in page and 'FINANCE_APPROVED' in page, page
        status, categories = request_json(base + '/categories')
        assert status == 200 and categories
        print('Frontend page and categories: PASS')

        status, created = request_json(base + '/expenses/drafts', 'POST', {
            'user_id': 2, 'category_id': 1, 'expense_date': '2026-10-30', 'amount': 450,
            'description': 'Workflow test', 'receipt_reference': 'TEST-RECEIPT'
        })
        assert status == 200 and created['status'] == 'DRAFT', created
        expense_id = created['expense_id']
        status, submitted = request_json(base + f'/expenses/{expense_id}/submit', 'POST', {'user_id': 2})
        assert status == 200 and submitted['status'] == 'SUBMITTED', submitted
        print('Draft to submitted: PASS')

        status, review = request_json(base + f'/expenses/{expense_id}/review', 'POST', {
            'approver_id': manager_id, 'decision': 'APPROVED', 'comments': 'Manager check'
        })
        assert status == 200 and review['status'] == 'MANAGER_APPROVED', review
        reimbursement_id = review['reimbursement_id']
        print('Manager approval: PASS')

        status, approved = request_json(base + f'/reimbursements/{reimbursement_id}/approve', 'POST', {
            'finance_user_id': finance_id, 'comments': 'Finance check'
        })
        assert status == 200 and approved['status'] == 'FINANCE_APPROVED', approved
        status, paid = request_json(base + f'/reimbursements/{reimbursement_id}/paid', 'POST', {
            'finance_user_id': finance_id, 'payment_method': 'Bank transfer', 'transaction_reference': 'TEST-001'
        })
        assert status == 200 and paid['status'] == 'PAID', paid
        print('Finance approval then payment: PASS')

        status, audit = request_json(base + f'/expenses/{expense_id}/audit?user_id=2')
        actions = [row['ACTION'] for row in audit]
        assert status == 200 and actions == ['DRAFT_CREATED', 'SUBMITTED', 'MANAGER_APPROVED', 'FINANCE_APPROVED', 'REIMBURSEMENT_PAID'], actions
        print('Audit history records every stage: PASS')

        status, rejected = request_json(base + '/expenses/drafts', 'POST', {
            'user_id': 2, 'category_id': 1, 'expense_date': '2026-10-30', 'amount': 100,
            'description': 'Rejection path test', 'receipt_reference': 'TEST-REJECT'
        })
        assert status == 200, rejected
        request_json(base + f"/expenses/{rejected['expense_id']}/submit", 'POST', {'user_id': 2})
        status, result = request_json(base + f"/expenses/{rejected['expense_id']}/review", 'POST', {
            'approver_id': manager_id, 'decision': 'REJECTED', 'comments': 'Not approved'
        })
        assert status == 200 and result['status'] == 'REJECTED' and result['reimbursement_id'] is None, result
        print('Manager rejection: PASS')
        print('End-to-end lifecycle: PASS')
    finally:
        if server is not None: server.should_exit = True
        if thread is not None: thread.join(timeout=5)
        listener.close()
        database.DATABASE_NAME = original
        if os.path.exists(path): os.remove(path)


if __name__ == '__main__':
    main()

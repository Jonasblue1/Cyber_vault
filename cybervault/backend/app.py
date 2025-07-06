"""
CyberVault Backend - REST API, Blockchain, AI Fraud Detection
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import http.server
import socketserver
import sqlite3
import hashlib
import json
import secrets
import base64
from urllib.parse import parse_qs, urlparse
from security import AESCipher, verify_pin
from identity import create_user_id, authenticate_user
from blockchain.blockchain import Block
from ai.model import predict_fraud
from post_quantum import encrypt_post_quantum, decrypt_post_quantum
from zkp import prove_loan_eligibility, verify_loan_proof

PORT = 8080
DB_FILE = 'cybervault.db'
AES_KEY = 'cybervault_super_secret_key'

# Initialize DB
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, pin_hash TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, data TEXT, status TEXT, fraud_flag INTEGER, timestamp TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS blockchain (id INTEGER PRIMARY KEY, block_hash TEXT, prev_hash TEXT, data TEXT, timestamp TEXT)''')
conn.commit()
conn.close()

class CyberVaultHandler(http.server.BaseHTTPRequestHandler):
    def _set_headers(self, code=200):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def _require_token(self):
        token = self.headers.get('Authorization', '').replace('Bearer ', '')
        if not token or len(token) < 10:
            self._set_headers(401)
            self.wfile.write(json.dumps({'error': 'Unauthorized'}).encode())
            return False
        return True

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode()
        data = json.loads(body) if body else {}
        path = self.path
        response = {}
        code = 200

        if path == '/register':
            username = data.get('username')
            pin = data.get('pin')
            if not username or not pin:
                response = {'error': 'Missing username or pin'}
                code = 400
            else:
                user_id = create_user_id(username)
                pin_hash = hashlib.sha256(pin.encode()).hexdigest()
                try:
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute('INSERT INTO users (id, pin_hash) VALUES (?, ?)', (user_id, pin_hash))
                    conn.commit()
                    conn.close()
                    response = {'status': 'registered', 'user_id': user_id}
                except sqlite3.IntegrityError:
                    response = {'error': 'User already exists'}
                    code = 409

        elif path == '/login':
            username = data.get('username')
            pin = data.get('pin')
            user_id = create_user_id(username)
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('SELECT pin_hash FROM users WHERE id=?', (user_id,))
            row = c.fetchone()
            conn.close()
            if row and verify_pin(pin, row[0]):
                token = base64.urlsafe_b64encode(secrets.token_bytes(24)).decode()
                response = {'status': 'authenticated', 'token': token, 'user_id': user_id}
            else:
                response = {'error': 'Invalid credentials'}
                code = 401

        elif path == '/transaction':
            if not self._require_token():
                return
            user_id = data.get('user_id')
            tx_data = data.get('data')
            timestamp = data.get('timestamp')
            if not user_id or not tx_data or not timestamp:
                response = {'error': 'Missing fields'}
                code = 400
            else:
                # Fraud detection
                fraud_flag = int(predict_fraud(tx_data))
                # Encrypt transaction data
                aes = AESCipher(AES_KEY)
                enc_data = aes.encrypt(json.dumps(tx_data)).hex()
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute('INSERT INTO transactions (user_id, data, status, fraud_flag, timestamp) VALUES (?, ?, ?, ?, ?)',
                          (user_id, enc_data, 'queued', fraud_flag, timestamp))
                conn.commit()
                conn.close()
                response = {'status': 'queued', 'fraud_flag': fraud_flag}

        elif path == '/blockchain/add':
            if not self._require_token():
                return
            block_data = data.get('data')
            prev_hash = data.get('prev_hash', '')
            timestamp = data.get('timestamp')
            if not block_data or not timestamp:
                response = {'error': 'Missing fields'}
                code = 400
            else:
                # Encrypt block data
                aes = AESCipher(AES_KEY)
                enc_block_data = aes.encrypt(json.dumps(block_data)).hex()
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute('SELECT block_hash FROM blockchain ORDER BY id DESC LIMIT 1')
                last = c.fetchone()
                prev_hash = last[0] if last else ''
                block = Block(index=0, previous_hash=prev_hash, timestamp=timestamp, data=enc_block_data)
                c.execute('INSERT INTO blockchain (block_hash, prev_hash, data, timestamp) VALUES (?, ?, ?, ?)',
                          (block.hash, prev_hash, enc_block_data, timestamp))
                conn.commit()
                conn.close()
                response = {'status': 'block_added', 'block_hash': block.hash}

        elif path == '/blockchain/validate':
            # Validate blockchain integrity
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('SELECT * FROM blockchain ORDER BY id ASC')
            blocks = c.fetchall()
            conn.close()
            valid = True
            prev_hash = ''
            for block in blocks:
                block_hash, block_prev_hash, enc_data, timestamp = block[1], block[2], block[3], block[4]
                if block_prev_hash != prev_hash:
                    valid = False
                    break
                prev_hash = block_hash
            response = {'valid': valid, 'length': len(blocks)}

        elif path == '/smartcontract/validate':
            # Placeholder: Validate loan terms (e.g., repayment schedule)
            contract = data.get('contract')
            # For demo, always valid
            response = {'valid': True}

        elif path == '/mesh/sync':
            # Peer-to-peer transaction sync (accepts a list of transactions)
            if not self._require_token():
                return
            txs = data.get('transactions', [])
            aes = AESCipher(AES_KEY)
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            for tx in txs:
                user_id = tx.get('user_id')
                tx_data = tx.get('data')
                timestamp = tx.get('timestamp')
                if user_id and tx_data and timestamp:
                    enc_data = aes.encrypt(json.dumps(tx_data)).hex()
                    c.execute('INSERT INTO transactions (user_id, data, status, fraud_flag, timestamp) VALUES (?, ?, ?, ?, ?)',
                              (user_id, enc_data, 'mesh', 0, timestamp))
            conn.commit()
            conn.close()
            response = {'status': 'mesh_sync_complete', 'count': len(txs)}

        elif path == '/zkp/prove':
            user_data = data.get('user_data')
            proof = prove_loan_eligibility(user_data)
            response = {'proof': proof}

        elif path == '/zkp/verify':
            proof = data.get('proof')
            valid = verify_loan_proof(proof)
            response = {'valid': valid}

        elif path == '/reputation/query':
            user_id = data.get('user_id')
            if not user_id:
                response = {'error': 'Missing user_id'}
                code = 400
            else:
                conn = sqlite3.connect(DB_FILE)
                from reputation.reputation import query_reputation_from_chain
                score = query_reputation_from_chain(user_id, AES_KEY, conn)
                conn.close()
                response = {'user_id': user_id, 'reputation': score}

        elif path == '/reputation/update':
            user_id = data.get('user_id')
            tx_history = data.get('tx_history', [])
            feedback = data.get('feedback', [])
            if not user_id:
                response = {'error': 'Missing user_id'}
                code = 400
            else:
                from reputation.reputation import calculate_reputation, store_reputation_on_chain
                score_hash, score = calculate_reputation(user_id, tx_history, feedback)
                conn = sqlite3.connect(DB_FILE)
                block_hash = store_reputation_on_chain(user_id, score, AES_KEY, conn)
                conn.close()
                response = {'user_id': user_id, 'reputation': score, 'block_hash': block_hash}

        else:
            response = {'error': 'Unknown endpoint'}
            code = 404

        self._set_headers(code)
        self.wfile.write(json.dumps(response).encode())

    def do_GET(self):
        path = urlparse(self.path).path
        response = {}
        code = 200
        # Serve API endpoints as before
        if path == '/status':
            response = {'status': 'CyberVault backend running'}
            self._set_headers(code)
            self.wfile.write(json.dumps(response).encode())
        elif path == '/blockchain':
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('SELECT * FROM blockchain')
            blocks = c.fetchall()
            conn.close()
            response = {'blockchain': blocks}
            self._set_headers(code)
            self.wfile.write(json.dumps(response).encode())
        elif path == '/transactions':
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('SELECT * FROM transactions')
            txs = c.fetchall()
            conn.close()
            response = {'transactions': txs}
            self._set_headers(code)
            self.wfile.write(json.dumps(response).encode())
        else:
            # Serve static frontend files for all other GET requests
            import os
            static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend'))
            file_path = path.lstrip('/') or 'index.html'
            abs_file = os.path.join(static_dir, file_path)
            if not os.path.isfile(abs_file):
                abs_file = os.path.join(static_dir, 'index.html')
            try:
                with open(abs_file, 'rb') as f:
                    content = f.read()
                if abs_file.endswith('.html'):
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                elif abs_file.endswith('.js'):
                    self.send_response(200)
                    self.send_header('Content-type', 'application/javascript')
                elif abs_file.endswith('.css'):
                    self.send_response(200)
                    self.send_header('Content-type', 'text/css')
                elif abs_file.endswith('.json'):
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                else:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/octet-stream')
                self.end_headers()
                self.wfile.write(content)
            except Exception:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'File not found')

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), CyberVaultHandler) as httpd:
        print(f"CyberVault backend running at http://localhost:{PORT}")
        httpd.serve_forever()

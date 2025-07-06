// CyberVault Frontend App JS
// Handles registration, login, transactions, offline queuing, and backend sync

const API_URL = (location.protocol === 'https:' ? 'https://' : 'http://') + 'localhost:8080';
let userId = null;
let token = null;
let csrfToken = null;
let sessionTimeout = null;

// CSRF token generation
function getCSRFToken() {
    let t = sessionStorage.getItem('csrfToken');
    if (!t) {
        t = Math.random().toString(36).substring(2) + Date.now();
        sessionStorage.setItem('csrfToken', t);
    }
    return t;
}

// Sanitize input
function sanitize(str) {
    return String(str).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
}

// IndexedDB setup for offline transaction queue
let db;
const DB_NAME = 'cybervault-db';
const TX_STORE = 'transactions';

function openDB() {
    return new Promise((resolve, reject) => {
        const req = indexedDB.open(DB_NAME, 1);
        req.onupgradeneeded = function(e) {
            db = e.target.result;
            if (!db.objectStoreNames.contains(TX_STORE)) {
                db.createObjectStore(TX_STORE, { autoIncrement: true });
            }
        };
        req.onsuccess = function(e) { db = e.target.result; resolve(); };
        req.onerror = function(e) { reject(e); };
    });
}

function queueTransaction(tx) {
    return new Promise((resolve, reject) => {
        const txObj = db.transaction([TX_STORE], 'readwrite').objectStore(TX_STORE);
        txObj.add(tx).onsuccess = resolve;
        txObj.onerror = reject;
    });
}

function getQueuedTransactions() {
    return new Promise((resolve) => {
        const txObj = db.transaction([TX_STORE], 'readonly').objectStore(TX_STORE);
        const req = txObj.getAll();
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => resolve([]);
    });
}

function clearQueuedTransactions() {
    return new Promise((resolve) => {
        const txObj = db.transaction([TX_STORE], 'readwrite').objectStore(TX_STORE);
        txObj.clear().onsuccess = resolve;
    });
}

// SHA-256 hashing for integrity
async function sha256(str) {
    const buf = new TextEncoder().encode(str);
    const hash = await crypto.subtle.digest('SHA-256', buf);
    return Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2, '0')).join('');
}

// PIN strength checker
document.getElementById('reg-pin').addEventListener('input', function() {
    const pin = this.value;
    const strengthDiv = document.getElementById('pin-strength');
    if (pin.length < 6 || pin.length > 8) {
        strengthDiv.textContent = 'PIN must be 6-8 digits.';
        strengthDiv.style.color = 'red';
    } else if (/^(\d)\1+$/.test(pin)) {
        strengthDiv.textContent = 'PIN cannot be repeated digits (e.g., 111111).';
        strengthDiv.style.color = 'red';
    } else if (/^(0123456|1234567|2345678|3456789|9876543|8765432|7654321|6543210)$/.test(pin)) {
        strengthDiv.textContent = 'PIN cannot be sequential digits.';
        strengthDiv.style.color = 'red';
    } else if (/^(19\d{2}|20\d{2})$/.test(pin)) {
        strengthDiv.textContent = 'PIN cannot be a year.';
        strengthDiv.style.color = 'red';
    } else {
        strengthDiv.textContent = 'Strong PIN.';
        strengthDiv.style.color = 'green';
    }
});

// UI Handlers
async function handleRegister(e) {
    e.preventDefault();
    const username = document.getElementById('reg-username').value.trim();
    const pin = document.getElementById('reg-pin').value.trim();
    if (!username || !pin) return;
    document.getElementById('auth-message').textContent = 'Registering...';
    const res = await fetch(API_URL + '/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCSRFToken() },
        body: JSON.stringify({ username: sanitize(username), pin: sanitize(pin) })
    });
    const data = await res.json();
    document.getElementById('auth-message').textContent = data.status || data.error;
}

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('login-username').value.trim();
    const pin = document.getElementById('login-pin').value.trim();
    if (!username || !pin) return;
    document.getElementById('auth-message').textContent = 'Logging in...';
    const res = await fetch(API_URL + '/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCSRFToken() },
        body: JSON.stringify({ username: sanitize(username), pin: sanitize(pin) })
    });
    const data = await res.json();
    if (data.status === 'authenticated') {
        userId = data.user_id;
        token = data.token;
        document.getElementById('auth-section').style.display = 'none';
        document.getElementById('main-section').style.display = '';
        document.getElementById('auth-message').textContent = '';
        startSessionTimeout();
        loadTransactions();
        loadBlockchain();
        syncQueuedTransactions();
    } else {
        document.getElementById('auth-message').textContent = data.error;
    }
}

async function handleTxSubmit(e) {
    e.preventDefault();
    const amount = document.getElementById('tx-amount').value;
    const type = document.getElementById('tx-type').value;
    const tx = {
        user_id: userId,
        data: { amount, type },
        timestamp: new Date().toISOString(),
        hash: await sha256(userId + amount + type + Date.now())
    };
    if (navigator.onLine) {
        document.getElementById('fraud-alert').textContent = 'Submitting...';
        const res = await fetch(API_URL + '/transaction', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token,
                'X-CSRF-Token': getCSRFToken()
            },
            body: JSON.stringify(tx)
        });
        const data = await res.json();
        if (data.fraud_flag) {
            document.getElementById('fraud-alert').textContent = 'Fraud detected!';
        } else {
            document.getElementById('fraud-alert').textContent = 'Transaction submitted.';
        }
        loadTransactions();
    } else {
        await queueTransaction(tx);
        document.getElementById('fraud-alert').textContent = 'Transaction queued offline.';
    }
    document.getElementById('tx-form').reset();
    startSessionTimeout();
}

async function syncQueuedTransactions() {
    if (!navigator.onLine) return;
    const txs = await getQueuedTransactions();
    for (const tx of txs) {
        await fetch(API_URL + '/transaction', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(tx)
        });
    }
    if (txs.length) await clearQueuedTransactions();
    loadTransactions();
}

async function loadTransactions() {
    const res = await fetch(API_URL + '/transactions');
    const data = await res.json();
    const txList = document.getElementById('tx-list');
    txList.innerHTML = '';
    (data.transactions || []).forEach(tx => {
        const li = document.createElement('li');
        li.textContent = JSON.stringify(tx);
        txList.appendChild(li);
    });
}

async function loadBlockchain() {
    const res = await fetch(API_URL + '/blockchain');
    const data = await res.json();
    const bcList = document.getElementById('blockchain-list');
    bcList.innerHTML = '';
    (data.blockchain || []).forEach(block => {
        const li = document.createElement('li');
        li.textContent = JSON.stringify(block);
        bcList.appendChild(li);
    });
}

document.getElementById('register-form').addEventListener('submit', handleRegister);
document.getElementById('login-form').addEventListener('submit', handleLogin);
document.getElementById('tx-form').addEventListener('submit', handleTxSubmit);
document.getElementById('logout-btn').addEventListener('click', () => {
    userId = null; token = null;
    document.getElementById('auth-section').style.display = '';
    document.getElementById('main-section').style.display = 'none';
});

window.addEventListener('online', syncQueuedTransactions);
window.addEventListener('DOMContentLoaded', openDB);

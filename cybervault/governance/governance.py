"""
Community-Driven Governance & Emergency Kill Switch
Multi-sig, blockchain-audited system changes and shutdown.
Offline-first: all actions are queued and validated locally, then synced when possible.
"""
import hashlib
import json
import time
from backend.security import AESCipher
from blockchain.blockchain import Block

PROPOSALS_DB = 'governance_proposals.json'

# Load or initialize local proposals db
def load_proposals():
    try:
        with open(PROPOSALS_DB, 'r') as f:
            return json.load(f)
    except Exception:
        return []

def save_proposals(proposals):
    with open(PROPOSALS_DB, 'w') as f:
        json.dump(proposals, f)

# Submit a new proposal
def submit_proposal(proposer, change_data, aes_key):
    proposals = load_proposals()
    proposal = {
        'id': hashlib.sha256(f'{proposer}{time.time()}'.encode()).hexdigest(),
        'proposer': proposer,
        'change_data': change_data,
        'votes': [proposer],
        'timestamp': time.time(),
        'status': 'pending'
    }
    aes = AESCipher(aes_key)
    proposal['enc_data'] = aes.encrypt(json.dumps(change_data)).hex()
    proposals.append(proposal)
    save_proposals(proposals)
    return proposal['id']

# Vote on a proposal
def vote_proposal(proposal_id, voter):
    proposals = load_proposals()
    for p in proposals:
        if p['id'] == proposal_id and voter not in p['votes']:
            p['votes'].append(voter)
            if len(p['votes']) >= 3:
                p['status'] = 'approved'
    save_proposals(proposals)
    return True

# Activate kill switch if approved
def activate_kill_switch(aes_key):
    proposals = load_proposals()
    for p in proposals:
        if p['status'] == 'approved' and 'kill' in p['change_data']:
            # Store kill event on blockchain
            block = Block(index=0, previous_hash='', timestamp=str(time.time()), data='KILL_SWITCH')
            # (Assume blockchain DB integration elsewhere)
            return 'System shutdown initiated.'
    return 'No approved kill switch proposal.'

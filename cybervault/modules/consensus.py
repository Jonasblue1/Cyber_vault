"""
Distributed, Self-Healing Consensus Blockchain
Hybrid proof-of-authority and proof-of-activity, auto-heals by comparing ledgers.
"""
import hashlib

# Compare local ledgers and repair corrupted blocks
def heal_blockchain(local_chain, peer_chains):
    # Find the most common valid chain among peers
    chains = [local_chain] + peer_chains
    chain_hashes = [hashlib.sha256(str(chain).encode()).hexdigest() for chain in chains]
    # Majority wins
    from collections import Counter
    most_common = Counter(chain_hashes).most_common(1)[0][0]
    for chain, h in zip(chains, chain_hashes):
        if h == most_common:
            return chain
    return local_chain

# Hybrid consensus: require both signatures and activity
# To be expanded with real signature/activity checks

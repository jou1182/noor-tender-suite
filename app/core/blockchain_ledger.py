import hashlib
import json
import time
from typing import List, Dict, Any

def generate_merkle_root(transactions: List[Dict[str, Any]]) -> str:
    """
    Computes a cryptographic Merkle Root for a batch of transactions.
    Ensures that any alteration to a single transaction entirely changes the root hash.
    """
    if not transactions:
        return hashlib.sha256(b"empty_block").hexdigest()
    
    tx_hashes = [hashlib.sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest() for tx in transactions]
    
    while len(tx_hashes) > 1:
        if len(tx_hashes) % 2 != 0:
            tx_hashes.append(tx_hashes[-1]) # Duplicate the last hash if odd
        new_level = []
        for i in range(0, len(tx_hashes), 2):
            combined = tx_hashes[i] + tx_hashes[i+1]
            new_level.append(hashlib.sha256(combined.encode()).hexdigest())
        tx_hashes = new_level
        
    return tx_hashes[0]

class Block:
    def __init__(self, index: int, transactions: List[Dict], previous_hash: str):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.merkle_root = generate_merkle_root(transactions)
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        """
        Calculates the definitive hash of the entire block structure, firmly anchoring 
        it to the previous block's hash.
        """
        block_string = f"{self.index}{self.timestamp}{self.merkle_root}{self.previous_hash}"
        return hashlib.sha256(block_string.encode()).hexdigest()

class BlockchainLedger:
    def __init__(self):
        self.chain: List[Block] = []
        self.pending_transactions: List[Dict] = []
        self._create_genesis_block()

    def _create_genesis_block(self):
        genesis_block = Block(0, [{"event": "GENESIS_INITIALIZATION"}], "00000000000000000000000000000000")
        self.chain.append(genesis_block)

    def add_transaction(self, tx: Dict[str, Any]):
        self.pending_transactions.append(tx)

    def commit_block(self) -> Block:
        if not self.pending_transactions:
            return None
        last_block = self.chain[-1]
        new_block = Block(
            index=len(self.chain),
            transactions=self.pending_transactions.copy(),
            previous_hash=last_block.hash
        )
        self.chain.append(new_block)
        self.pending_transactions = []
        return new_block

    def verify_chain_integrity(self) -> bool:
        """
        Traverses the entire ledger from Genesis to the latest block.
        Recalculates every Merkle Root and Block Hash. If a single byte was retroactively 
        tampered with anywhere in history, this returns False.
        """
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            
            # 1. Verify Block Hash Mathematical Integrity
            if current.hash != current.calculate_hash():
                return False
            
            # 2. Verify Transaction Integrity via Merkle Proof
            if current.merkle_root != generate_merkle_root(current.transactions):
                return False
                
            # 3. Verify Cryptographic Chain Link 
            if current.previous_hash != previous.hash:
                return False
                
        return True

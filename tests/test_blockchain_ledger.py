import unittest
from app.core.blockchain_ledger import BlockchainLedger

class TestBlockchainLedger(unittest.TestCase):
    def setUp(self):
        self.ledger = BlockchainLedger()

    def test_genesis_block_creation(self):
        self.assertEqual(len(self.ledger.chain), 1)
        genesis = self.ledger.chain[0]
        self.assertEqual(genesis.index, 0)
        self.assertEqual(genesis.previous_hash, "00000000000000000000000000000000")
        
    def test_block_chaining_and_merkle_root(self):
        # Add legitimate transactions
        self.ledger.add_transaction({"event": "NCR_APPROVED", "ncr_id": "NCR-123"})
        self.ledger.add_transaction({"event": "DOSSIER_SIGNED", "hash": "abc456"})
        
        block = self.ledger.commit_block()
        
        self.assertEqual(block.index, 1)
        self.assertEqual(len(block.transactions), 2)
        
        # Verify the chain correctly links the new block's previous_hash to genesis block hash
        genesis = self.ledger.chain[0]
        self.assertEqual(block.previous_hash, genesis.hash)
        
        # Verify complete network integrity
        self.assertTrue(self.ledger.verify_chain_integrity())

    def test_retroactive_tampering_invalidates_merkle_proof(self):
        # 1. Commit a valid block
        self.ledger.add_transaction({"event": "NCR_APPROVED", "ncr_id": "NCR-123"})
        self.ledger.commit_block()
        
        # System is currently valid
        self.assertTrue(self.ledger.verify_chain_integrity())
        
        # 2. Simulate a malicious internal actor directly tampering with the database record 
        #    changing the NCR ID retroactively.
        tampered_block = self.ledger.chain[1]
        tampered_block.transactions[0]["ncr_id"] = "NCR-999_TAMPERED"
        
        # 3. Verify the Ledger detects the manipulation via Merkle Root mismatch
        self.assertFalse(self.ledger.verify_chain_integrity())
        
    def test_retroactive_tampering_invalidates_chain_hash(self):
        self.ledger.add_transaction({"data": "secure_data"})
        self.ledger.commit_block()
        self.ledger.add_transaction({"data": "more_secure_data"})
        self.ledger.commit_block()
        
        # Malicious actor changes the hash manually to bypass Merkle checks
        self.ledger.chain[1].hash = "fake_recalculated_hash"
        
        # Ledger catches the chain disruption
        self.assertFalse(self.ledger.verify_chain_integrity())

if __name__ == "__main__":
    unittest.main()

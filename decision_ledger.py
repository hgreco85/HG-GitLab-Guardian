import hashlib
import json
import time
from typing import Any, Dict, List, Optional


class DecisionLedgerBlock:
    def __init__(
        self,
        index: int,
        previous_hash: str,
        timestamp: float,
        decision: Dict[str, Any],
        nonce: int = 0,
        hash_val: Optional[str] = None,
    ):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.decision = decision
        self.nonce = nonce
        self.hash = hash_val if hash_val else self.calculate_hash()

    def calculate_hash(self) -> str:
        block_data = {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "decision": self.decision,
            "nonce": self.nonce,
        }
        serialized = json.dumps(block_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "decision": self.decision,
            "nonce": self.nonce,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DecisionLedgerBlock":
        return cls(
            index=data["index"],
            previous_hash=data["previous_hash"],
            timestamp=data["timestamp"],
            decision=data["decision"],
            nonce=data.get("nonce", 0),
            hash_val=data.get("hash"),
        )


class DecisionLedger:
    GENESIS_PREV_HASH = "0" * 64

    def __init__(self):
        self.chain: List[DecisionLedgerBlock] = []

    def initialize_genesis(self, genesis_decision: Optional[Dict[str, Any]] = None, timestamp: float = 0.0) -> DecisionLedgerBlock:
        if self.chain:
            raise ValueError("Ledger already initialized.")
        initial_decision = genesis_decision if genesis_decision is not None else {"event": "GENESIS"}
        genesis_block = DecisionLedgerBlock(
            index=0,
            previous_hash=self.GENESIS_PREV_HASH,
            timestamp=timestamp,
            decision=initial_decision,
        )
        self.chain.append(genesis_block)
        return genesis_block

    def record_decision(self, decision: Dict[str, Any], timestamp: Optional[float] = None) -> DecisionLedgerBlock:
        if not self.chain:
            raise ValueError("Genesis block must be created before recording decisions.")
        
        last_block = self.chain[-1]
        block_timestamp = timestamp if timestamp is not None else time.time()
        new_block = DecisionLedgerBlock(
            index=last_block.index + 1,
            previous_hash=last_block.hash,
            timestamp=block_timestamp,
            decision=decision,
        )
        self.chain.append(new_block)
        return new_block

    def verify_integrity(self) -> bool:
        if not self.chain:
            return True

        genesis = self.chain[0]
        if genesis.index != 0:
            return False
        if genesis.previous_hash != self.GENESIS_PREV_HASH:
            return False
        if genesis.hash != genesis.calculate_hash():
            return False

        for i in range(1, len(self.chain)):
            prev_block = self.chain[i - 1]
            curr_block = self.chain[i]

            if curr_block.index != prev_block.index + 1:
                return False
            if curr_block.previous_hash != prev_block.hash:
                return False
            if curr_block.hash != curr_block.calculate_hash():
                return False

        return True

    def export_ledger(self) -> List[Dict[str, Any]]:
        return [block.to_dict() for block in self.chain]

    @classmethod
    def load_ledger(cls, ledger_data: List[Dict[str, Any]]) -> "DecisionLedger":
        ledger = cls()
        ledger.chain = [DecisionLedgerBlock.from_dict(d) for d in ledger_data]
        return ledger

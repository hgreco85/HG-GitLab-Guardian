"""Immutable cryptographic ledger for tracking agent decisions and post-code lifecycle actions."""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, List, Optional


class DecisionBlock:
    def __init__(
        self,
        index: int,
        timestamp: float,
        step: str,
        actor: str,
        action: str,
        payload: Dict[str, Any],
        previous_hash: str,
    ):
        self.index = index
        self.timestamp = timestamp
        self.step = step
        self.actor = actor
        self.action = action
        self.payload = payload
        self.previous_hash = previous_hash
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        record = {
            "index": self.index,
            "timestamp": self.timestamp,
            "step": self.step,
            "actor": self.actor,
            "action": self.action,
            "payload": self.payload,
            "previous_hash": self.previous_hash,
        }
        encoded = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "step": self.step,
            "actor": self.actor,
            "action": self.action,
            "payload": self.payload,
            "previous_hash": self.previous_hash,
            "hash": self.hash,
        }


class DecisionLedger:
    """Tamper-evident chain recording all lifecycle events and agent diagnoses."""

    def __init__(self):
        self.chain: List[DecisionBlock] = []
        # Genesis block
        genesis = DecisionBlock(
            index=0,
            timestamp=0.0,
            step="GENESIS",
            actor="SYSTEM",
            action="INITIALIZE_LEDGER",
            payload={"message": "GitLab Guardian Decision Ledger Initialized"},
            previous_hash="0" * 64,
        )
        self.chain.append(genesis)

    def record(self, step: str, actor: str, action: str, payload: Dict[str, Any]) -> DecisionBlock:
        prev_hash = self.chain[-1].hash
        block = DecisionBlock(
            index=len(self.chain),
            timestamp=time.time(),
            step=step,
            actor=actor,
            action=action,
            payload=payload,
            previous_hash=prev_hash,
        )
        self.chain.append(block)
        return block

    def verify(self) -> bool:
        """Verifies integrity of entire chain."""
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i - 1]
            if curr.previous_hash != prev.hash:
                return False
            if curr.compute_hash() != curr.hash:
                return False
        return True

    def export(self) -> List[Dict[str, Any]]:
        return [b.to_dict() for b in self.chain]

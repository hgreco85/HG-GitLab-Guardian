import hashlib
import json
import time
from typing import Any, Dict, List, Optional


def canonical_json(data: Any) -> str:
    """Serialize data deterministically to a canonical JSON string."""
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def compute_hash(data: Any) -> str:
    """Compute SHA-256 hash of canonical JSON string."""
    serialized = canonical_json(data)
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


class DecisionEntry:
    """A single record in the decision ledger with cryptographic linkage."""

    def __init__(
        self,
        index: int,
        timestamp: float,
        decision_type: str,
        payload: Dict[str, Any],
        prev_hash: str,
        current_hash: Optional[str] = None,
    ):
        self.index = index
        self.timestamp = timestamp
        self.decision_type = decision_type
        self.payload = payload
        self.prev_hash = prev_hash
        self.current_hash = current_hash or self.calculate_hash()

    def get_hashable_dict(self) -> Dict[str, Any]:
        """Return the deterministic dictionary representing entry state for hashing."""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "decision_type": self.decision_type,
            "payload": self.payload,
            "prev_hash": self.prev_hash,
        }

    def calculate_hash(self) -> str:
        """Calculate the SHA-256 hash of this entry."""
        return compute_hash(self.get_hashable_dict())

    def verify(self) -> bool:
        """Verify that current_hash matches the actual hash of content."""
        return self.current_hash == self.calculate_hash()

    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.get_hashable_dict(),
            "current_hash": self.current_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DecisionEntry":
        return cls(
            index=data["index"],
            timestamp=data["timestamp"],
            decision_type=data["decision_type"],
            payload=data["payload"],
            prev_hash=data["prev_hash"],
            current_hash=data.get("current_hash"),
        )


class DecisionLedger:
    """An append-only, tamper-evident cryptographic decision ledger."""

    GENESIS_PREV_HASH = "0" * 64

    def __init__(self):
        self.entries: List[DecisionEntry] = []

    def append(self, decision_type: str, payload: Dict[str, Any], timestamp: Optional[float] = None) -> DecisionEntry:
        """Record a new decision into the ledger."""
        index = len(self.entries)
        prev_hash = self.entries[-1].current_hash if self.entries else self.GENESIS_PREV_HASH
        actual_ts = timestamp if timestamp is not None else time.time()

        entry = DecisionEntry(
            index=index,
            timestamp=actual_ts,
            decision_type=decision_type,
            payload=payload,
            prev_hash=prev_hash,
        )
        self.entries.append(entry)
        return entry

    def verify_integrity(self) -> bool:
        """
        Perform deterministic cryptographic verification of the ledger's
        immutability, hash chain linkage, and tamper resistance.
        """
        if not self.entries:
            return True

        for i, entry in enumerate(self.entries):
            # 1. Verify index sequence
            if entry.index != i:
                return False

            # 2. Verify previous hash pointer
            expected_prev_hash = self.GENESIS_PREV_HASH if i == 0 else self.entries[i - 1].current_hash
            if entry.prev_hash != expected_prev_hash:
                return False

            # 3. Verify entry self-integrity
            if not entry.verify():
                return False

        return True

    def get_merkle_root(self) -> str:
        """Compute deterministic Merkle tree root of all entry hashes."""
        if not self.entries:
            return compute_hash([])

        current_hashes = [entry.current_hash for entry in self.entries]
        while len(current_hashes) > 1:
            if len(current_hashes) % 2 != 0:
                current_hashes.append(current_hashes[-1])
            next_level = []
            for i in range(0, len(current_hashes), 2):
                combined = current_hashes[i] + current_hashes[i + 1]
                next_level.append(hashlib.sha256(combined.encode('utf-8')).hexdigest())
            current_hashes = next_level

        return current_hashes[0]

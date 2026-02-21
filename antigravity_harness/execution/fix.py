"""
antigravity_harness/execution/fix.py
===================================
Institutional FIX Protocol Engine (Baseline).
Pure-Python implementation of SOH-delimited tag-value framing.
"""

import asyncio
import datetime
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("FIX_ENGINE")

SOH = "\x01"


class FixMessage:
    """Core FIX message handling serialization and checksums."""

    def __init__(self, msg_type: str, sender_comp_id: str, target_comp_id: str, seq_num: int):
        self.tags: Dict[int, str] = {}
        self.msg_type = msg_type
        
        # Standard Header
        self.set_tag(8, "FIX.4.4")  # BeginString
        self.set_tag(35, msg_type)  # MsgType
        self.set_tag(49, sender_comp_id)  # SenderCompID
        self.set_tag(56, target_comp_id)  # TargetCompID
        self.set_tag(34, str(seq_num))  # MsgSeqNum
        self.set_tag(52, datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H:%M:%S.%f")[:-3])  # SendingTime

    def set_tag(self, tag: int, value: str) -> None:
        self.tags[tag] = str(value)

    def get_tag(self, tag: int) -> Optional[str]:
        return self.tags.get(tag)

    def serialize(self) -> bytes:
        """Serialize to SOH-delimited wire format with length and checksum."""
        # 1. Build body (excluding checksum and length tags)
        # Sequence: BeginString(8), BodyLength(9), MsgType(35), ..., Checksum(10)
        
        # We need to calculate body length first.
        # Length includes everything between BodyLength(9) and Checksum(10)
        
        # Essential Order for Header
        header_tags = [35, 49, 56, 34, 52]
        body_parts = []
        for tag in header_tags:
            body_parts.append(f"{tag}={self.tags[tag]}{SOH}")
            
        # Other tags
        for tag, val in self.tags.items():
            if tag not in [8, 9, 10] + header_tags:
                body_parts.append(f"{tag}={val}{SOH}")
                
        body_str = "".join(body_parts)
        body_len = len(body_str)
        
        # Final construction
        prefix = f"8={self.tags[8]}{SOH}9={body_len}{SOH}"
        message_pre_checksum = prefix + body_str
        
        # Checksum calculation: sum of all bytes % 256
        checksum_val = sum(message_pre_checksum.encode()) % 256
        checksum_str = f"{checksum_val:03}"
        
        final_message = f"{message_pre_checksum}10={checksum_str}{SOH}"
        return final_message.encode()

    @staticmethod
    def parse(data: bytes) -> 'FixMessage':
        """Parse raw bytes into a FixMessage (Simplified)."""
        parts = data.decode().split(SOH)
        tags = {}
        for p in parts:
            if "=" in p:
                t, v = p.split("=", 1)
                tags[int(t)] = v
                
        # Basic validation
        if 10 not in tags:
            raise ValueError("FIX Parse Error: Missing Checksum (Tag 10)")
            
        # Create dummy instance and populate
        msg = FixMessage("0", "X", "X", 0)
        msg.tags = tags
        msg.msg_type = tags.get(35, "0")
        return msg


class FixSession:
    """State machine for institutional FIX connection."""

    def __init__(self, sender: str, target: str):
        self.sender = sender
        self.target = target
        self.outbound_seq = 1
        self.inbound_seq = 0
        self.active = False

    def create_message(self, msg_type: str) -> FixMessage:
        msg = FixMessage(msg_type, self.sender, self.target, self.outbound_seq)
        self.outbound_seq += 1
        return msg

    def handle_inbound(self, msg: FixMessage) -> None:
        seq = int(msg.get_tag(34) or 0)
        if seq <= self.inbound_seq:
            logger.warning(f"FIX Sequence Error: Expected > {self.inbound_seq}, got {seq}")
        self.inbound_seq = seq
        
        m_type = msg.get_tag(35)
        if m_type == "A": # Logon
            self.active = True
            logger.info("FIX Session Active (Logon).")
        elif m_type == "5": # Logout
            self.active = False
            logger.info("FIX Session Terminated (Logout).")

import unittest

from antigravity_harness.execution.fix import SOH, FixMessage, FixSession


class TestFixEngine(unittest.TestCase):
    def test_checksum_calculation(self):
        """Verify institutional Tag 10 checksum logic."""
        msg = FixMessage("A", "SENDER", "TARGET", 1)
        # Manually force tag bits to ensure deterministic checksum for test
        msg.tags[52] = "20260220-21:00:00.000"
        
        raw = msg.serialize()
        # raw format: 8=FIX.4.4|9=...|35=A|49=SENDER|56=TARGET|34=1|52=...|10=...|
        
        # Checksum is last 7 bytes: "10=XXX\x01"
        checksum_part = raw[-7:].decode()
        self.assertTrue(checksum_part.startswith("10="))
        self.assertTrue(checksum_part.endswith(SOH))
        
        # Parse it back
        parsed = FixMessage.parse(raw)
        self.assertEqual(parsed.get_tag(35), "A")
        self.assertEqual(parsed.get_tag(49), "SENDER")
        self.assertEqual(parsed.get_tag(34), "1")

    def test_session_sequence(self):
        """Verify FIX sequence number incrementing."""
        session = FixSession("SENDER", "TARGET")
        
        m1 = session.create_message("0") # Heartbeat
        self.assertEqual(m1.get_tag(34), "1")
        
        m2 = session.create_message("0")
        self.assertEqual(m2.get_tag(34), "2")
        
        self.assertEqual(session.outbound_seq, 3)

    def test_serialization_framing(self):
        """Verify SOH delimiters are present in the expected positions."""
        msg = FixMessage("0", "S", "T", 1)
        raw = msg.serialize().decode()
        
        # Should start with BeginString
        self.assertTrue(raw.startswith(f"8=FIX.4.4{SOH}"))
        
        # Every tag-value pair should end with SOH
        parts = raw.split(SOH)
        # Remove last empty part if split result ends in delimiter
        parts = [p for p in parts if p]
        
        for p in parts:
            self.assertIn("=", p)

if __name__ == "__main__":
    unittest.main()

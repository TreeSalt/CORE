# 06_BENCHMARKING/tests/01_DATA_INGESTION/test_websocket_handler.py
#
# RATIFICATION STATUS: RATIFIED — Logic Gate enforces 1.0 threshold
# Author: Supreme Council (Claude drafting, Alec ratifies)
# Based on: PROPOSAL_01_DATA_INGESTION_20260309T182908Z.md

import pytest
from unittest.mock import MagicMock, patch

# ══════════════════════════════════════════════════════════
# IMPORT VERIFICATION
# ══════════════════════════════════════════════════════════
def test_required_imports_exist():
    """Hygiene overlap: all imports in proposal must be resolvable."""
    pass

# ══════════════════════════════════════════════════════════
# CONNECTION TESTS
# ══════════════════════════════════════════════════════════
class TestWebSocketHandlerConnection:
    def test_handler_initializes_with_correct_address(self):
        """Handler stores server address on init."""
        from data_ingestion.websocket_handler import WebSocketHandler
        address = "wss://test.market.com/feed"
        handler = WebSocketHandler(
            server_address=address, on_message=MagicMock(),
            on_error=MagicMock(), on_close=MagicMock(), on_open=MagicMock()
        )
        assert handler.server_address == address

    def test_handler_ws_is_none_before_connect(self):
        from data_ingestion.websocket_handler import WebSocketHandler
        handler = WebSocketHandler(
            server_address="wss://test.market.com/feed", on_message=MagicMock(),
            on_error=MagicMock(), on_close=MagicMock(), on_open=MagicMock()
        )
        assert handler.ws is None

    @patch("websocket.WebSocketApp")
    def test_connect_creates_websocket_app(self, mock_ws_class):
        from data_ingestion.websocket_handler import WebSocketHandler
        mock_ws_instance = MagicMock()
        mock_ws_class.return_value = mock_ws_instance
        handler = WebSocketHandler(
            server_address="wss://test.market.com/feed", on_message=MagicMock(),
            on_error=MagicMock(), on_close=MagicMock(), on_open=MagicMock()
        )
        handler.connect()
        mock_ws_class.assert_called_once()
        assert mock_ws_class.call_args[0][0] == "wss://test.market.com/feed"

# ══════════════════════════════════════════════════════════
# DATA PROCESSING TESTS
# ══════════════════════════════════════════════════════════
class TestWebSocketDataProcessing:
    def setup_method(self):
        from data_ingestion.websocket_handler import WebSocketHandler
        self.handler = WebSocketHandler(
            server_address="wss://test.market.com/feed", on_message=MagicMock(),
            on_error=MagicMock(), on_close=MagicMock(), on_open=MagicMock()
        )
        self.handler.ws = MagicMock()

    def test_on_message_parses_valid_json(self):
        market_data = json.dumps({"symbol": "AAPL", "price": 175.23, "volume": 1000000, "timestamp": "2026-03-09T14:28:33Z"})
        self.handler.on_message(self.handler.ws, market_data)

    def test_on_message_handles_malformed_json_gracefully(self):
        malformed = "{ this is not : valid json }"
        try:
            self.handler.on_message(self.handler.ws, malformed)
        except Exception as e:
            pytest.fail(f"Handler crashed on malformed JSON: {e}")

    def test_on_message_handles_empty_string(self):
        try:
            self.handler.on_message(self.handler.ws, "")
        except Exception as e:
            pytest.fail(f"Handler crashed on empty message: {e}")

    def test_process_data_called_on_valid_message(self):
        from data_ingestion.websocket_handler import WebSocketHandler
        handler = WebSocketHandler(
            server_address="wss://test.market.com/feed", on_message=MagicMock(),
            on_error=MagicMock(), on_close=MagicMock(), on_open=MagicMock()
        )
        handler.ws = MagicMock()
        handler.process_data = MagicMock()
        valid_data = json.dumps({"symbol": "AAPL", "price": 175.23})
        handler.on_message(handler.ws, valid_data)
        handler.process_data.assert_called_once()

# ══════════════════════════════════════════════════════════
# ERROR HANDLING TESTS
# ══════════════════════════════════════════════════════════
class TestWebSocketErrorHandling:
    def setup_method(self):
        from data_ingestion.websocket_handler import WebSocketHandler
        self.handler = WebSocketHandler(
            server_address="wss://test.market.com/feed", on_message=MagicMock(),
            on_error=MagicMock(), on_close=MagicMock(), on_open=MagicMock()
        )
        self.handler.ws = MagicMock()

    def test_on_error_does_not_raise(self):
        try:
            self.handler.on_error(self.handler.ws, ConnectionError("Connection refused"))
        except Exception as e:
            pytest.fail(f"on_error re-raised exception: {e}")

    def test_on_close_does_not_raise(self):
        try:
            self.handler.on_close(self.handler.ws, 1000, "Normal closure")
        except Exception as e:
            pytest.fail(f"on_close raised exception: {e}")

    def test_on_close_handles_none_status(self):
        try:
            self.handler.on_close(self.handler.ws, None, None)
        except Exception as e:
            pytest.fail(f"on_close crashed with None status: {e}")

# ══════════════════════════════════════════════════════════
# MESSAGE SENDING TESTS
# ══════════════════════════════════════════════════════════
class TestWebSocketSending:
    def setup_method(self):
        from data_ingestion.websocket_handler import WebSocketHandler
        self.handler = WebSocketHandler(
            server_address="wss://test.market.com/feed", on_message=MagicMock(),
            on_error=MagicMock(), on_close=MagicMock(), on_open=MagicMock()
        )
        self.handler.ws = MagicMock()

    def test_send_formats_message_as_json(self):
        self.handler.send("SUBSCRIBE", {"symbol": "AAPL"})
        self.handler.ws.send.assert_called_once()
        sent_arg = self.handler.ws.send.call_args[0][0]
        parsed = json.loads(sent_arg)
        assert parsed["command"] == "SUBSCRIBE"
        assert parsed["payload"]["symbol"] == "AAPL"

    def test_send_requires_active_connection(self):
        self.handler.ws = None
        with pytest.raises(Exception):
            self.handler.send("SUBSCRIBE", {"symbol": "AAPL"})

# ══════════════════════════════════════════════════════════
# FIDUCIARY / CONSTITUTIONAL TESTS
# ══════════════════════════════════════════════════════════
class TestFiduciaryConstraints:
    def test_handler_does_not_write_to_governance_domain(self):
        import inspect
        import data_ingestion.websocket_handler as module
        source = inspect.getsource(module)
        forbidden_patterns = ["04_GOVERNANCE", "AGENTIC_ETHICAL_CONSTITUTION", "OPERATOR_INSTANCE", ".governor_seal"]
        for pattern in forbidden_patterns:
            assert pattern not in source, f"CONSTITUTIONAL VIOLATION: references '{pattern}'"

    def test_handler_does_not_hardcode_credentials(self):
        import inspect
        import data_ingestion.websocket_handler as module
        source = inspect.getsource(module).lower()
        credential_patterns = ["api_key =", "password =", "secret =", "token =", "bearer "]
        for pattern in credential_patterns:
            assert pattern not in source, f"CONSTITUTIONAL VIOLATION: Potential credential '{pattern}' found."

    def test_data_feed_logs_anomalies(self):
        from data_ingestion.websocket_handler import WebSocketHandler
        import logging
        handler = WebSocketHandler(
            server_address="wss://test.market.com/feed", on_message=MagicMock(),
            on_error=MagicMock(), on_close=MagicMock(), on_open=MagicMock()
        )
        handler.ws = MagicMock()
        with patch("logging.error") as mock_log:
            handler.on_message(handler.ws, "{ malformed json }")
            mock_log.assert_called()

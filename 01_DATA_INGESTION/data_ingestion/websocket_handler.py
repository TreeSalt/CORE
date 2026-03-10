import websocket
import ssl
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WebSocketHandler:
    def __init__(self, server_address, on_message=None, on_error=None, on_close=None, on_open=None):
        self.server_address = server_address
        # Renamed to _cb suffix to avoid overwriting instance methods
        self._on_message_cb = on_message
        self._on_error_cb   = on_error
        self._on_close_cb   = on_close
        self._on_open_cb    = on_open
        self.ws = None

    def connect(self):
        self.ws = websocket.WebSocketApp(
            self.server_address,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            self.process_data(data)
        except json.JSONDecodeError as e:
            logging.error(f"JSONDecodeError: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")

    def process_data(self, data):
        logging.info(f"Received data: {data}")

    def on_error(self, ws, error):
        logging.error(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        logging.info(f"WebSocket closed: {close_status_code}, {close_msg}")

    def on_open(self, ws):
        logging.info("WebSocket opened")
        self.send("SUBSCRIBE", {"symbol": "AAPL"})

    def send(self, command, payload):
        if self.ws is None:
            raise RuntimeError("Cannot send: WebSocket is not connected.")
        message = {"command": command, "payload": payload}
        self.ws.send(json.dumps(message))

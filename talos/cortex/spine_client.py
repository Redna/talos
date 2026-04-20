import json
import socket


class SpineError(Exception):
    pass


class SpineClient:
    def __init__(self, socket_path: str):
        self.socket_path = socket_path

    def _send(self, method: str, params: dict) -> dict:
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(300)
                s.connect(self.socket_path)
                request = {
                    "jsonrpc": "2.0",
                    "method": method,
                    "params": params,
                    "id": 1,
                }
                s.sendall(json.dumps(request).encode())
                response = b""
                while True:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                result = json.loads(response.decode())
                if "error" in result:
                    raise SpineError(
                        result["error"].get("message", str(result["error"]))
                    )
                return result.get("result", {})
        except SpineError:
            raise
        except Exception as e:
            raise SpineError(str(e))

    def think(self, focus, tools, hud_data) -> dict:
        return self._send(
            "think", {"focus": focus, "tools": tools, "hud_data": hud_data}
        )

    def tool_result(self, tool_call_id, output, success) -> dict:
        return self._send(
            "tool_result",
            {"tool_call_id": tool_call_id, "output": output, "success": success},
        )

    def request_fold(self, synthesis) -> dict:
        return self._send("request_fold", {"synthesis": synthesis})

    def request_restart(self, reason) -> dict:
        return self._send("request_restart", {"reason": reason})

    def emit_event(self, event_type, payload):
        try:
            self._send("emit_event", {"event_type": event_type, "payload": payload})
        except SpineError:
            pass

    def send_message(self, channel, text) -> dict:
        return self._send("send_message", {"channel": channel, "text": text})

"""
Lightweight HTTP Server and API for Regex-to-Minimized-DFA Web Visualizer.

Provides:
- Static file serving for web UI (web/index.html, styles.css, app.js)
- REST API:
  - POST /api/convert: Run full pipeline on given regex
  - POST /api/simulate: Run string simulation on regex automata
  - GET  /api/samples: List benchmark expressions

Zero external dependencies (uses standard library http.server).
"""

import sys
import os
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from regex_to_dfa.visualizer import run_pipeline, export_dot_nfa, export_dot_dfa, export_dot_min_dfa
from regex_to_dfa.simulator import AutomatonSimulator
from regex_to_dfa.parser import RegexParseError


WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")


class RegexDFAHandler(SimpleHTTPRequestHandler):
    """Custom request handler supporting API endpoints and web UI."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/samples":
            self._send_json(200, {
                "samples": [
                    {"regex": "(a|b)*abb", "title": "Ends with 'abb'", "desc": "Classic compiler token specification"},
                    {"regex": "(a|b)*a(a|b)", "title": "2nd-to-last is 'a'", "desc": "Nondeterministic lookahead branching"},
                    {"regex": "a(b|c)*", "title": "Prefix with alternatives", "desc": "Common lexer token prefix matching"},
                    {"regex": "(0|1)*00(0|1)*", "title": "Contains '00'", "desc": "Binary pattern matching with loops"},
                    {"regex": "(a*b*)*", "title": "Nested Star Closures", "desc": "Tests multi-level epsilon loop reduction"},
                    {"regex": "(a|eps)b*", "title": "Optional Prefix (eps)", "desc": "Epsilon empty string handling"},
                    {"regex": "a+b?", "title": "Plus (+) & Optional (?)", "desc": "Extended regular expression operators"},
                    {"regex": "(a|b)*abb(a|b)*", "title": "Contains Substring 'abb'", "desc": "Intermediate substring matching"}
                ]
            })
            return

        # Serve static web files
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

        try:
            body = json.loads(post_body)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON payload."})
            return

        if parsed.path == "/api/convert":
            regex_input = body.get("regex", "").strip()
            if not regex_input:
                self._send_json(400, {"error": "Regular expression string is required."})
                return

            try:
                pipeline_result = run_pipeline(regex_input)
                self._send_json(200, {
                    "success": True,
                    "data": pipeline_result.to_dict()
                })
            except RegexParseError as e:
                self._send_json(400, {"success": False, "error": f"Regex Syntax Error: {str(e)}"})
            except Exception as e:
                self._send_json(500, {"success": False, "error": f"Internal Error: {str(e)}"})
            return

        elif parsed.path == "/api/simulate":
            regex_input = body.get("regex", "").strip()
            test_string = body.get("string", "")

            if not regex_input:
                self._send_json(400, {"error": "Regular expression string is required."})
                return

            try:
                pipeline_result = run_pipeline(regex_input)
                sim_result = AutomatonSimulator.test_string(
                    test_string,
                    pipeline_result.nfa,
                    pipeline_result.dfa,
                    pipeline_result.min_dfa
                )
                self._send_json(200, {
                    "success": True,
                    "simulation": sim_result
                })
            except Exception as e:
                self._send_json(500, {"success": False, "error": str(e)})
            return

        self._send_json(404, {"error": "Endpoint not found."})

    def _send_json(self, status_code: int, data: dict):
        response_bytes = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(response_bytes)


def start_server(port: int = 8080, host: str = "127.0.0.1"):
    candidate_ports = [port, 8080, 5000, 3000, 8888]
    httpd = None
    actual_port = port

    for p in candidate_ports:
        try:
            server_address = (host, p)
            httpd = HTTPServer(server_address, RegexDFAHandler)
            actual_port = p
            break
        except (PermissionError, OSError):
            continue

    if httpd is None:
        # Bind to any free port assigned by OS
        server_address = (host, 0)
        httpd = HTTPServer(server_address, RegexDFAHandler)
        actual_port = httpd.server_port

    url = f"http://{host}:{actual_port}"
    print(f"\n=======================================================")
    print(f"  Regex to Minimized DFA Visualizer Web App Running!")
    print(f"  Open in your browser: {url}")
    print(f"=======================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    start_server(port=port)

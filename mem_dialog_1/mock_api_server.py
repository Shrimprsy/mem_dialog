import http.server
import json
import socketserver
from urllib.parse import urlparse, parse_qs

class MockLLMHandler(http.server.BaseHTTPRequestHandler):
    def _set_response(self, status_code=200, content_type='application/json'):
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.end_headers()

    def do_POST(self):
        if self.path == '/chat/completions':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            # 模拟 LLM 响应
            response = {
                "id": "chatcmpl-test123",
                "object": "chat.completion",
                "created": 1234567890,
                "model": data.get("model", "gpt-3.5-turbo"),
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "这是一个模拟的 AI 响应。你好！我可以帮你进行对话。"
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30
                }
            }

            self._set_response()
            self.wfile.write(json.dumps(response).encode('utf-8'))

        elif self.path == '/embeddings':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            # 模拟 embedding 响应 (1536维向量)
            embedding = [0.1] * 1536
            response = {
                "id": "emb-test123",
                "object": "list",
                "data": [{
                    "object": "embedding",
                    "embedding": embedding,
                    "index": 0
                }],
                "model": data.get("model", "text-embedding-ada-002")
            }

            self._set_response()
            self.wfile.write(json.dumps(response).encode('utf-8'))

        else:
            self._set_response(404, 'text/html')
            self.wfile.write(b'Not Found')

def run_mock_server(port=8080):
    handler = MockLLMHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Mock LLM server running on port {port}")
        print(f"API URLs: http://localhost:{port}/chat/completions")
        print(f"API URLs: http://localhost:{port}/embeddings")
        httpd.serve_forever()

if __name__ == "__main__":
    run_mock_server()
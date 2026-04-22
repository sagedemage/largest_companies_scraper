import socket
import ssl
from urllib.parse import urlparse
from typing import Optional, Dict, Tuple
import gzip
import io
import certifi

class HTTPSClient:
    def __init__(self):
        self.context = ssl.create_default_context(cafile=certifi.where())

    def get_content(self, url, custom_headers: Optional[Dict[str, str]] = None) -> Tuple[Optional[str], Optional[int]]:
        # Parse the URL
        parsed = urlparse(url)
        host = parsed.hostname
        path = parsed.path or '/'
        if parsed.query:
            path += '?' + parsed.query
    
        # Create and secure the socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        secure_sock = self.context.wrap_socket(sock, server_hostname=host)

        try:
            # Connect and send request
            secure_sock.connect((host, 443))

            # Build headers
            headers = {
                'Host': host,
                'User-Agent': 'Mozilla/5.0 (Custom Socket Client)',
                'Accept': 'text/html,application/xhtml+xml',
                'Connection': 'close'
            }

            if custom_headers != None:
                headers.update(custom_headers)
        
            # Contruct request
            request_lines = [f"GET {path} HTTP/1.1"]
            request_lines.extend([f"{k}: {v}" for k, v in headers.items()])
            request_lines.append('')
            request = '\r\n'.join(request_lines) + '\r\n'

            secure_sock.send(request.encode())

            # Receive response
            response = b""
            while True:
                chunk = secure_sock.recv(8192)
                if not chunk:
                    break
                response += chunk
            
            # Separate headers from body
            header_end = response.find(b'\r\n\r\n')
            if header_end == -1:
                None, None
            
            headers_raw = response[:header_end].decode()

            # Parse headers into dict
            headers = self._parse_headers(headers_raw)
            
            # Parse status from first line
            status_line = response[:header_end].decode()
            parts = status_line.split()
            status_code = int(parts[1]) if len(parts) >= 2 else None

            if status_code > 399 and status_code < 500:
                return None, status_code

            body = ""
            body_b = response[header_end + 4:] # Skip \r\n\r\n

            # Handle chunked encoding if present
            transfer_encoding = headers.get('transfer-encoding', '').lower()
            if transfer_encoding == "chunked":
                body_b = self._decode_chunked(body_b)

            body = self._decode_body(body_b, headers)
        
            return body, status_code
    
        except Exception as e:
            print(f"Error: {e}")
            print(f"URL: {url}")
            return None
    
        finally:
            secure_sock.close()
    
    @staticmethod
    def _parse_headers(headers_raw: str) -> Dict[str, str]:
        """Parse HTTP headers into dictionary"""
        headers = {}
        lines = headers_raw.split('\r\n')
        for line in lines[1:]:
            if ': ' in line:
                key, value = line.split(': ', 1)
                headers[key.lower()] = value
        
        return headers

    @staticmethod
    def _decode_chunked(data: bytes) -> bytes:
        """Simple chunked transfer decoding"""
        result = b""
        pos = 0
        while pos < len(data):
            # Find end of chunk size line
            crlf = data.find(b'\r\n', pos)
            if crlf == -1:
                break

            # Get chunk size (hex)
            chunk_size = int(data[pos:crlf], 16)
            pos = crlf + 2

            if chunk_size == 0:
                break

            # Read chunk data
            result += data[pos:pos + chunk_size]
            pos += chunk_size + 2 # Skip chunk data and trailing CRLF

        return result

    @staticmethod
    def _decode_body(body_b: bytes, headers: Dict[str, str]) -> str:
        """Decode body based on Content-Encoding header"""
        body = ""
        content_encoding = headers.get('content-encoding', '').lower()
        if content_encoding == "gzip":
            try:
                # Decompress gzip data
                with gzip.GzipFile(fileobj=io.BytesIO(body_b)) as gz:
                    decompressed = gz.read()
                    body = decompressed.decode('utf-8', errors='ignore')
            except Exception as e:
                print(f"Gzip decompression failed: {e}")
        else:
            body = body_b.decode('utf-8', errors='ignore')
        return body
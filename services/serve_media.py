"""
Simple HTTP server to serve downloaded media files
"""

import os
import logging
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MediaHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="/home/ubuntu/social-media-archive-project/media_storage", **kwargs)
    
    def end_headers(self):
        # Add CORS headers for web access
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

def main():
    port = int(os.getenv('MEDIA_SERVER_PORT', 8000))
    media_path = Path(os.getenv('MEDIA_STORAGE_PATH', '/home/ubuntu/social-media-archive-project/media_storage'))
    
    if not media_path.exists():
        media_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created media storage directory: {media_path}")
    
    logger.info(f"Starting media server on port {port}")
    logger.info(f"Serving files from: {media_path}")
    
    with socketserver.TCPServer(("", port), MediaHandler) as httpd:
        logger.info(f"Media server running at http://localhost:{port}/")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Media server stopped")

if __name__ == "__main__":
    main()

"""
Basic tests for the health check endpoint.
"""

import sys
import os
import json
import unittest
from bottle import HTTPResponse

# Add parent directory to path so we can import the main module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the health_check function from web_game
from web_game import health_check

class TestHealthCheck(unittest.TestCase):
    """Tests for the health check endpoint"""
    
    def test_health_check_returns_ok(self):
        """Test that health check returns status ok"""
        result = health_check()
        
        # If it's an HTTPResponse, get the body
        if isinstance(result, HTTPResponse):
            # Convert bytes to string if needed
            body = result.body
            if isinstance(body, bytes):
                body = body.decode('utf-8')
            # Parse the JSON body
            data = json.loads(body)
        else:
            # Already a dictionary
            data = result
        
        self.assertEqual(data['status'], 'ok', "Health check should return status 'ok'")
        self.assertIn('timestamp', data, "Health check should include timestamp")
        self.assertIn('version', data, "Health check should include version")
        self.assertIn('db_connection', data, "Health check should include db_connection status")

if __name__ == '__main__':
    unittest.main() 
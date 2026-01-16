"""Config Loader - Load environment and config files"""
import os
from dotenv import load_dotenv
from pathlib import Path

def load_config():
    """Load .env file and return config dict"""
    load_dotenv()
    return {
        'VAULT_PATH': os.getenv('VAULT_PATH', './vault'),
        'GMAIL_CLIENT_ID': os.getenv('GMAIL_CLIENT_ID'),
        'GMAIL_CLIENT_SECRET': os.getenv('GMAIL_CLIENT_SECRET'),
        'XERO_CLIENT_ID': os.getenv('XERO_CLIENT_ID'),
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
    }

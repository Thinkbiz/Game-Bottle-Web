import logging
import os
import sys
import json
from logging.handlers import RotatingFileHandler
from datetime import datetime
from config import LOG_DIR, LOG_LEVEL, LOG_TO_STDOUT, LOG_FORMAT, LOG_MAX_SIZE, LOG_BACKUP_COUNT

# Ensure logs directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Create loggers dictionary to store named loggers
loggers = {}

class JsonFormatter(logging.Formatter):
    """Format logs as JSON for better parsing in container environments"""
    def format(self, record):
        log_record = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'name': record.name,
            'message': record.getMessage(),
        }
        
        # Add extra fields if available
        if hasattr(record, 'session_id'):
            log_record['session_id'] = record.session_id
        if hasattr(record, 'player_name'):
            log_record['player_name'] = record.player_name
        if hasattr(record, 'request_path'):
            log_record['request_path'] = record.request_path
            
        # Add exception info if available
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

class SessionAdapter(logging.LoggerAdapter):
    """Adapter to add session and player info to log records"""
    def process(self, msg, kwargs):
        # Check if extra dict exists
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        
        # Add session_id if available in this adapter but not in extras
        if hasattr(self, 'session_id') and 'session_id' not in kwargs['extra']:
            kwargs['extra']['session_id'] = self.session_id
            
        # Add player_name if available in this adapter but not in extras
        if hasattr(self, 'player_name') and 'player_name' not in kwargs['extra']:
            kwargs['extra']['player_name'] = self.player_name
            
        return msg, kwargs

def get_logger(name):
    """Get or create a logger with the specified name"""
    if name in loggers:
        return loggers[name]
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Prevent log propagation to avoid duplicate entries
    logger.propagate = False
    
    # Clear any existing handlers (to avoid duplicates on reloads)
    if logger.handlers:
        logger.handlers = []
    
    # Create file handler with rotation for this specific logger
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, f'{name}.log'),
        maxBytes=LOG_MAX_SIZE,
        backupCount=LOG_BACKUP_COUNT
    )
    
    if LOG_FORMAT.lower() == 'json':
        file_formatter = JsonFormatter()
    else:
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Add stdout handler if enabled
    if LOG_TO_STDOUT:
        stdout_handler = logging.StreamHandler(sys.stdout)
        
        if LOG_FORMAT.lower() == 'json':
            stdout_formatter = JsonFormatter()
        else:
            stdout_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
        stdout_handler.setFormatter(stdout_formatter)
        logger.addHandler(stdout_handler)
    
    # Store in cache and return
    loggers[name] = logger
    return logger

def get_session_logger(name, session_id=None, player_name=None):
    """Get a logger that includes session information"""
    logger = get_logger(name)
    adapter = SessionAdapter(logger, {})
    
    if session_id:
        adapter.session_id = session_id
    if player_name:
        adapter.player_name = player_name
        
    return adapter

# Create default loggers
game_logger = get_logger('game')
game_state_logger = get_logger('game_state')
api_logger = get_logger('api')
db_logger = get_logger('database')
web_logger = get_logger('web')

# Export loggers
__all__ = ['get_logger', 'get_session_logger', 'game_logger', 
           'game_state_logger', 'api_logger', 'db_logger', 'web_logger'] 
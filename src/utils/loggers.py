#!/usr/bin/python3
# Author: Liu Renke

#standard imports
from datetime import datetime as dt
import inspect
import json
import logging
from logging.config import dictConfig
import os
from pathlib import Path
import shutil
import sys
import time


LOG_ROOT_DIR = Path.cwd()/'logs'
LOG_DIR = LOG_ROOT_DIR/dt.now().strftime("%Y%m%d-%H%M%S")
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": '%(asctime)s [%(module)s: %(lineno)-3d] %(levelname)-5s >>> %(message)s',
        },
        "brief": {
            "format": '%(asctime)s %(levelname)-7s >>> %(message)s',
        },
    },
    "handlers": {
        "server_log_file": {
            "class": "logging.FileHandler",
            "formatter": "verbose",
            "filename": LOG_DIR/"server.log",
            "mode": "a",
        },
        "app_log_file": {
            "class": "logging.FileHandler",
            "formatter": "verbose",
            "filename": LOG_DIR/"app.log",
            "mode": "a",
        },
        "query_log_file": {
            "class": "logging.FileHandler",
            "formatter": "verbose",
            "filename": LOG_DIR/f'query.log',
            "mode": "a",
        },
        "chat_engine_log_file": {
            "class": "logging.FileHandler",
            "formatter": "verbose",
            "filename": LOG_DIR/f'chat_engine.log',
            "mode": "a",
        },
        "error_console": {
            "class": "logging.StreamHandler",
            "formatter": "brief",
            "level": "ERROR",
        },
        "app_console": {
            "class": "logging.StreamHandler",
            "formatter": "brief",
            "level": "INFO",
        }
    },
    "root": {
        "handlers": ["server_log_file"],
        "level": "DEBUG",
    },
    "loggers": {
        "uvicorn": {
            "handlers": ["server_log_file", "error_console"],
            "level": "WARNING",
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["server_log_file", "error_console"],
            "level": "WARNING",
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["server_log_file", "error_console"],
            "level": "WARNING",
            "propagate": False,
        },
        "fastapi": {
            "handlers": ["app_log_file", "error_console"],
            "level": "WARNING",
            "propagate": False,
        },
        "app_logger": {
            "handlers": ["app_log_file", "app_console"],
            "level": "DEBUG",
            "propagate": False
        },
        "llama_index.core.chat_engine.condense_plus_context": {
            "handlers": ["chat_engine_log_file"],
            "level": "DEBUG",
            "propagate": False
        },        
        "query_logger": {
            "handlers": ["query_log_file", "app_console"],
            "level": "DEBUG",
            "propagate": False
        }
    },
}


def setup_logging(keep:int=5):
    # verify log directories
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    # prune obsolete log folders (sub-directories) from root directory
    folders = [f.path for f in os.scandir(LOG_ROOT_DIR) if f.is_dir()]
    folders.sort(key=lambda x: os.path.getmtime(LOG_ROOT_DIR / x), reverse=True)
    # remove obsolete log files/folders
    folders_to_keep = folders[:keep]
    for folder in folders:
        if folder not in folders_to_keep:
            folder_path = LOG_ROOT_DIR / folder
            shutil.rmtree(folder_path)
    # reset all logger's config
    dictConfig(LOG_CONFIG)


class QueryLogger:
    def __init__(self):
        self.logger = logging.getLogger('rag_server')

    def log_query(self, query_pl, response, source_nodes, query_time, response_time):
        log_entry = {
            'session_id': query_pl.session_id,
            'query': query_pl.query,
            'response': response,
            'source_nodes': [
                {
                    'document_name': node.metadata.get('document_name', 'Unknown'),
                    'subsection': node.metadata.get('subsection', 'Unknown'),
                    'start_page': node.metadata.get('start_page', 'N/A'),
                    'end_page': node.metadata.get('end_page', 'N/A')
                } for node in source_nodes
            ],
            'query_time': query_time,
            'response_time': response_time
        }
        
        # Log as JSON for easy parsing
        self.logger.info(json.dumps(log_entry))

    def log_feedback(self, feedback):
        log_entry = {
            'turn_id': feedback.turn_id,
            'session_id': feedback.session_id,
            'feedback': feedback.feedback,
            'timestamp': dt.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.logger.info(json.dumps(log_entry))
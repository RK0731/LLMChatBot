#!/usr/bin/python3
# Author: Liu Renke

"""
FastAPI application to serve simple chat and RAG chat endpoints.
"""
# Standard imports
import argparse
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime as dt
from fastapi import (
    APIRouter, BackgroundTasks, FastAPI, HTTPException, 
    Request, Response, status, WebSocket, WebSocketDisconnect,
    Query
    )
from fastapi.responses import (
    HTMLResponse, ORJSONResponse, FileResponse, StreamingResponse, 
    PlainTextResponse, JSONResponse
    )
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import logging
from pathlib import Path
from pydantic import BaseModel
import sys
from typing import TYPE_CHECKING, Optional, List, Dict, Union 
import uuid
import uvicorn
# project imports
from src.api_models import *
from src.chat_engines import Converse_Bedrock
from src.utils.loggers import setup_logging
from src.utils.proj_paths import *
from src.utils.utils import (
    parse_config, 
    BUDDHA
)

# =========================================================================================================
# Initialization of web application backend, including chat engine, databases, ect.
# =========================================================================================================
setup_logging()
logger = logging.getLogger("app_logger")
CONFIG = parse_config(BACKEND_CONFIG)

# executed before the application start up
@asynccontextmanager
async def lifespan(app: FastAPI):
    global CONVERSE_ENGINE
    CONVERSE_ENGINE = initialize_converse_engine(logger=logger, config=CONFIG)
    logger.info(f"RenkeBot backend initialization completed, ready for handling requests.")
    logger.info(BUDDHA)
    yield
# create the application with lifespan events, refer to https://fastapi.tiangolo.com/advanced/events/
app = FastAPI(lifespan=lifespan)

def initialize_converse_engine(logger:logging.Logger, config:dict) -> Converse_Bedrock:
    return Converse_Bedrock(logger=logger, config=config)

# =========================================================================================================
# HTTP/HTTPS API endpoints
# =========================================================================================================
@app.post("/simple_chat", status_code=status.HTTP_200_OK)
async def simple_chat(req_pl: SimpleChatQuery, request: Request) -> SimpleChatResponse:
    try:
        # log the user query
        logger.info(f"Received [{sys._getframe().f_code.co_name}] request from {request.client}: '{req_pl.query}'.")
        # assign new seesion_id if not included in the request payload
        if not req_pl.session_id: 
            req_pl.session_id = str(uuid.uuid4()) # generate an id for the new session
            logger.info(f"Generated new session id: {req_pl.session_id}")
        # invoke chat engine to complete the conversation
        _res = await asyncio.to_thread(CONVERSE_ENGINE.chat, req_pl.query, req_pl.session_id)
        # generate the return response
        response= SimpleChatResponse(message=_res, session_id=req_pl.session_id)
        return response
    except Exception as e:
        logger.error(f"Failed to reply. Error: {e}.")
        raise HTTPException(status_code=getattr(e, 'status_code', status.HTTP_500_INTERNAL_SERVER_ERROR), detail=str(e))

# =========================================================================================================
# Start application and listen to specified port
# =========================================================================================================
if __name__ == '__main__':
    # arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', default='dev', 
                        choices=['dev', 'prod'], 
                        help='Serve APIs under dev (http) or production mode')
    args = parser.parse_args()
    # verify hosting environment
    if args.mode == 'dev':
        _config = CONFIG['fastapi']['dev']
        # Start application under HTTP protocol, enabling reload
        uvicorn.run("main:app", host=_config['host'], port=_config['port'], reload=True)
    elif args.mode == 'prod':
        _config = CONFIG['fastapi']['prod']
        # Start application under HTTP protocol
        uvicorn.run("main:app", host=_config['host'], port=_config['port'])        

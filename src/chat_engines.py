import os
import boto3
from typing import TYPE_CHECKING, Dict, List, Union
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory, RedisChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_aws import ChatBedrockConverse
#from langchain_redis import RedisChatMessageHistory
from langchain_core.runnables import RunnableConfig
import logging
import redis
import yaml
# project imports
from src.utils.proj_paths import *
from src.utils.exceptions import *
from src.utils.utils import get_service_config


class Converse_Bedrock():
    def __init__(self, logger:logging.Logger, config_path:Union[str,Path]=BACKEND_CONFIG):
        """Initializes the chat engine with Bedrock Chat Model."""
        try:
            self.logger = logger
            # parse config file
            self._engine_config = get_service_config(config_path, 'converse_engine')
            print(self._engine_config)
            self._redis_config = get_service_config(config_path, 'redis')
            # create llm and chain
            self.llm = ChatBedrockConverse(**self._engine_config)
            self.chain = self.get_conversation_chain()
            self.logger.info(f"Successfully initialized LLM instance and chat chain, config: {self._engine_config}")
        except Exception as e:
            raise AppInitializationError(f"Failed to initialize LLM instance, error: {e}")
        try:
            # verify database connection
            self._verify_redis()
        except Exception as e:
            raise
        
    def get_conversation_chain(self):
        """Defines the full conversation chain with prompt and history."""
        # Define the Chat Prompt Template
        with open(CONVERSE_SYS_PROMPT, 'r') as f:
            _sys_prompt = f.read()
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", _sys_prompt),
                    MessagesPlaceholder(variable_name="history"), # This is where the chat history will be injected
                    ("user", "{input}"), # This is where the new user input will go
                ]
            )
        # Create the basic chain: Prompt -> Model -> Output Parser
        _core_chain = prompt | self.llm | StrOutputParser()
        # Add history management to the chain
        _chain_with_history = RunnableWithMessageHistory(
            runnable=_core_chain, 
            get_session_history=self.get_session_history, 
            input_messages_key="input", 
            history_messages_key="history",
        )
        return _chain_with_history

    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """Gets or creates a chat message history for a given session ID."""
        return RedisChatMessageHistory(session_id, url=self._redis_url, ttl=self._redis_config['ttl'])

    def _verify_redis(self):
        """verify the existence of Redis database"""
        try:
            r = redis.Redis(
                host=self._redis_config['host'], 
                port=self._redis_config['port'], 
                db=self._redis_config['db'], 
                socket_connect_timeout=1
            )
            r.ping()
            self.logger.info("Successfully connected to Redis server.")
        except redis.exceptions.ConnectionError as e:
            raise AppInitializationError(f"Could not connect to Redis server: {e}")
        except redis.exceptions.RedisError as e:
            raise UndefinedDatabaseError(f"An error occurred with Redis: {e}")

    @property
    def _redis_url(self):
        return f"redis://{self._redis_config['host']}:{self._redis_config['port']}/{self._redis_config['db']} "

    def chat(self, input:str, session_id:str) -> Union[None, str]:
        """
        Start or continue (if session_id is provided) a conversation
        """
        config: RunnableConfig = {"configurable": {"session_id":session_id}}
        # validate user input and chat session
        if not input.strip():
            return
        # Invoke the conversation chain with the user input and session config
        _response = self.chain.invoke({"input": input}, config=config)
        return _response

    def start_chat(self):
        """
        Starts an interactive chat session in terminal to test the conversation capability.
        """
        print("\n----- AWS Bedrock Chat Engine (Beta) -----")
        print(f"Model: {self.llm.model_id}")
        _quit_kws = ["exit", "q", "quit"]
        print(f"Type <{", ".join(_quit_kws)}> to end the chat.\n")
        # Use a fixed session ID for a single conversation thread
        session_id = "interactive_0" 
        # Configuration for the session history
        config: RunnableConfig = {"configurable": {"session_id": session_id}}
        while True:
            try:
                input = input("You: ").strip()
                if input.lower() in _quit_kws:
                    print("Ending chat. Goodbye!")
                    break
                if not input:
                    continue
                # Invoke the conversation chain with the user input and session config
                ai_response = self.chain.invoke({"input": input}, config=config,)
                print(f"AI: {ai_response}")
            except Exception as e:
                print(f"\nAn error occurred: {e}")
                print("Please check your AWS credentials, Bedrock access, and model ID.")
                break

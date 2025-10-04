import os
import boto3
from typing import Dict, List
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_aws import ChatBedrockConverse
from langchain_core.runnables import RunnableConfig
import logging
import yaml
# project imports
from src.utils.proj_paths import *
from src.utils.utils import parse_config


class Converse_Bedrock():
    def __init__(self, logger:logging.Logger):
        """Initializes the chat engine with Bedrock Chat Model."""
        try:
            # parse config file
            _config = parse_config(BACKEND_CONFIG)['converse_engine']
            # Using ChatBedrockConverse which utilizes the Converse API
            self.llm = ChatBedrockConverse(**_config)
            # to be replaced, in-memory chat history
            self.store: Dict[str, ChatMessageHistory] = {}
            logger.info(f"Successfully initialized LLM instance, config: {_config}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM instance, error: {e}")


    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """Gets or creates a chat message history for a given session ID."""
        return self.store.setdefault(session_id, ChatMessageHistory())


    def get_conversation_chain(self):
        """Defines the full conversation chain with prompt and history."""
        # 3.1. Define the Chat Prompt Template
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful and friendly AI assistant powered by Amazon Bedrock. "
                    "Keep your answers concise and relevant to the conversation history."
                ),
                # This is where the chat history will be injected
                MessagesPlaceholder(variable_name="history"),
                # This is where the new user input will go
                ("human", "{input}"),
            ]
        )
        # 3.3. Create the basic chain: Prompt -> Model -> Output Parser
        chain = prompt | self.llm | StrOutputParser()
        # 3.4. Add history management to the chain
        conversation_chain = RunnableWithMessageHistory(
            chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="history",
        )
        return conversation_chain

    def start_chat(self):
        """
        Starts the interactive chat session for testing purpose.
        """
        print("\n--- Starting AWS Bedrock Chat Engine ---")
        print(f"Model: {self.llm.model_id}")
        print("Type 'bye' or 'exit' to end the chat.\n")
        # Use a fixed session ID for a single conversation thread
        session_id = "user-123" 
        conversation_chain = self.get_conversation_chain()
        # Configuration for the session history
        config: RunnableConfig = {"configurable": {"session_id": session_id}}
        while True:
            try:
                user_input = input("You: ").strip()
                if user_input.lower() in ["bye", "exit", "q", "quit"]:
                    print("Ending chat. Goodbye!")
                    break
                if not user_input:
                    continue

                # Invoke the conversation chain with the user input and session config
                ai_response = conversation_chain.invoke(
                    {"input": user_input},
                    config=config,
                )
                
                print(f"AI: {ai_response}")

            except Exception as e:
                print(f"\nAn error occurred: {e}")
                print("Please check your AWS credentials, Bedrock access, and model ID.")
                break

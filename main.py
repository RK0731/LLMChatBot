import logging
from src.chat_engine import Converse_Bedrock
from src.utils.utils import enable_stream

logger=logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
enable_stream(logger=logger)

x = Converse_Bedrock(logger)
x.start_chat()

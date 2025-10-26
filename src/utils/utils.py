import boto3
import logging
import os
from pathlib import Path
import requests
from requests.exceptions import ConnectTimeout, RequestException
from typing import Union, List, Dict
import yaml

# General purpose logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def enable_stream(logger:logging.Logger):
    """ Add stream handler to logger to show log in console
    """
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s [%(module)s: %(lineno)-3d] %(levelname)-5s >>> %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

def verify_aws_connection():
    """
    Verifies the AWS connection by calling the STS GetCallerIdentity API.
    """
    try:
        # Create a low-level client for the STS service
        sts_client = boto3.client('sts')
        # Call the GetCallerIdentity API
        _fm_response = sts_client.get_caller_identity()
        logger.debug(f"Successfully connected to AWS. Account ID: {_fm_response['Account']}, User ARN: {_fm_response['Arn']}")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to AWS. {e}")
        return False

def list_bedrock_foundation_models():
    """
    Lists all available foundation models in Amazon Bedrock using the default AWS configuration.
    """
    try:
        # Create a Boto3 client for the Bedrock service
        # Boto3 will automatically use your default credentials and region
        bedrock_client = boto3.client(service_name='bedrock')
        logger.info("Listing available Amazon Bedrock foundation models...")
        # Call the list_foundation_models API
        _fm_response = bedrock_client.list_foundation_models()
        #_em_response = bedrock_client.list_foundation_models(byOutputModality='EMBEDDING')
        # fundational models
        # Check if the 'modelSummaries' key exists in the _fm_response
        if 'modelSummaries' in _fm_response:
            models = _fm_response['modelSummaries']
            if not models:
                logger.error("No foundation models found!")
                return
            # logger.debug a formatted list of the models
            _str = f"Found {len(models)} foundation/embedding models.\n"
            for model in models:
                _str += f"* Model ID: {model['modelId']}:\n "
                _str += f"   Provider: {model['providerName']}, Input Modalities: {', '.join(model.get('inputModalities', []))}, Output Modalities: {', '.join(model.get('outputModalities', []))}\n"
            logger.info(_str)
        else:
            logger.warning("AWS response did not contain 'modelSummaries'.")
    except Exception as e:
        logger.debug(f"An error occurred: {e}")

def detect_environment() -> str:
    """
    Detects the current running environment.

    Returns:
        A string indicating the environment: 'ec2', 'docker', or 'local'.
    """
    # 1. Check for Docker Container Environment
    # The /.dockerenv file is a common indicator of running inside a Docker container.
    if os.path.exists("/.dockerenv"):
        return "docker"
    # 2. Check for AWS EC2 Environment
    # The EC2 instance metadata service is only available on EC2 instances.
    # We use a very short timeout to avoid blocking the application for too long.
    # NOTE: Modern IMDS requires a token, but a simple connection attempt 
    # to the IP is often enough to detect the environment for this purpose.
    IMDS_ENDPOINT = "http://169.254.169.254/latest/meta-data/"
    try:
        # A quick attempt to connect to the well-known IMDS IP
        requests.get(IMDS_ENDPOINT, timeout=0.1) 
        # If the connection succeeds, it's highly likely to be EC2
        return "ec2"
    except ConnectTimeout:
        # The request times out or is blocked (e.g., when not on EC2)
        pass
    except RequestException:
        # Catch other connection errors (e.g., DNS error, connection refused, etc.)
        pass
    # 3. Default to Local Environment
    return "local"

def parse_config(config_path: Union[str,Path]) -> dict:
    """
    Load and parse config file from specified path
    """
    # validate path
    if isinstance(config_path, str) and len(config_path) == 0:
        raise ValueError("Must provide valid path to app configs")
    elif isinstance(config_path, Path) and not config_path.exists():
        raise ValueError("Must provide valid path to app configs")
    # load config file(s)
    config = yaml.safe_load(open(config_path))
    return config

def get_service_config(config_path: Union[str,Path], service_name: str, default_env: str = 'local') -> dict:
    """
    Parses a YAML config file, selects the correct host/IP based on the 
    detected environment, and returns the simplified service configuration.

    Args:
        config_filepath (str): Path to the YAML configuration file.
        service_name (str): The name of the service (e.g., 'redis').
        default_env (str): The fallback key to use if the environment 
                           is not explicitly defined in the config's host list.

    Returns:
        dict: The simplified configuration for the service with a single 'host' key.
        
    Raises:
        FileNotFoundError: If the config file is not found.
        KeyError: If the service or host key structure is not found in the config.
    """
    # 1. Get the specific service config
    full_config = parse_config(config_path)
    service_config:dict = full_config.get(service_name)
    if not service_config:
        raise KeyError(f"Service '{service_name}' not found in configuration.")
    
    # 2. Extract the host mapping, return original config if there's no such key
    host_mapping = service_config.pop('host', None)
    # Handle case where 'host' is already a string (simple config)
    if isinstance(host_mapping, str):
        service_config['host'] = host_mapping
        return service_config
    elif not host_mapping:
        return service_config

    # 3. Determine the correct host key
    # Environment names in this logic are 'ec2', 'container', 'local'.
    host_key = detect_environment()
    host_address = host_mapping.get(host_key)
    # If the environment-specific key isn't in the config, use a fallback
    if host_address is None:
        host_address = host_mapping.get(default_env)
    if host_address is None:
        raise KeyError(f"Could not find a host address for environment '{host_key}' or default '{default_env}'. Available keys: {list(host_mapping.keys())}")
    # 4. Construct the final simplified config
    service_config['host'] = host_address
    return service_config

BUDDHA = """
                     _ooOoo_
                    o8888888o
                    88" . "88
                    (| -_- |)
                    O\\  =  /O
                 ____/`---'\\____
               .'  \\\\|     |//  `.
              /  \\\\|||  :  |||//  \\
             /  _||||| -:- |||||-  \\
             |   | \\\\\\  -  /// |   |
             | \\_|  ''\\---/''  |   |
             \\  .-\\__  `-`  ___/-. /
           ___`. .'  /--.--\\  `. . __
        ."" '<  `.___\\_<|>_/___.'  >'"".
       | | :  `- \\`.;`\\ _ /`;.`/ - ` : | |
       \\  \\ `-.   \\_ __\\ /__ _/   .-` /  /
  ======`-.____`-.___\\_____/___.-`____.-'======
                     `=---='
  菩提本无树, 明镜亦非台, 本来无BUG, 何必常修改
  .............................................
"""

if __name__ == '__main__':
    enable_stream(logger)
    # Run the function
    list_bedrock_foundation_models()
    # Run the function to test the connection
    if verify_aws_connection():
        logger.debug("Your AWS credentials are valid.")
    else:
        logger.debug("Please check your AWS credentials and configuration.")

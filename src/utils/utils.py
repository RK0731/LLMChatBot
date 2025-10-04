import boto3
import logging
from pathlib import Path
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

def parse_config(config_path: Union[str,Path]):
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



if __name__ == '__main__':
    enable_stream(logger)
    # Run the function
    list_bedrock_foundation_models()
    # Run the function to test the connection
    if verify_aws_connection():
        logger.debug("Your AWS credentials are valid.")
    else:
        logger.debug("Please check your AWS credentials and configuration.")

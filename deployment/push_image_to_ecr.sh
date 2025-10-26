#!/usr/bin/env bash
# Author: Suzanna Sia, Liu Renke

# Configuration - Edit these variables
AWS_ACCOUNT="992382490092"
AWS_PROFILE="default"
ECR_REPO="m07-d-ecr-repo"
MFA_SERIAL_NUMBER="arn:aws:iam::992382490092:mfa/macbook"  # Replace with your MFA ARN

get_temp_credentials() {
    local token_code=$1
    
    echo "Getting temporary credentials..."
    credentials=$(aws sts get-session-token \
        --serial-number $MFA_SERIAL_NUMBER \
        --token-code $token_code \
		--profile $AWS_PROFILE)

    
    if [ $? -ne 0 ]; then
        echo "Error getting temporary credentials"
        exit 1
    fi
    
    # Extract credentials
    export AWS_ACCESS_KEY_ID=$(echo $credentials | jq -r '.Credentials.AccessKeyId')
    export AWS_SECRET_ACCESS_KEY=$(echo $credentials | jq -r '.Credentials.SecretAccessKey')
    export AWS_SESSION_TOKEN=$(echo $credentials | jq -r '.Credentials.SessionToken')
    
    # Save to file for later use
    echo "export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID" > ~/.aws/temp_credentials
    echo "export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY" >> ~/.aws/temp_credentials
    echo "export AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN" >> ~/.aws/temp_credentials
    
    echo "Temporary credentials saved to ~/.aws/temp_credentials"
}

ecr_login() {
    echo "Getting ECR login password..."
    aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
    
    if [ $? -ne 0 ]; then
        echo "Error logging into ECR"
        exit 1
    fi
    
    echo "Successfully logged into ECR"
}

docker_push() {
	docker tag $DOCKER_IMAGE_ID $AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/$ECR_REPO:$DOCKER_IMAGE_VERSION
	docker push $AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/$ECR_REPO:$DOCKER_IMAGE_VERSION
}

# Check if an argument was provided
# Define the default Docker Image Name
DEFAULT_DOCKER_IMAGE_ID="rag-app"
if [ -z "$1" ]; then
   # Prompt the user for the MFA code if no argument is given
  echo "Please provide your MFA code to generate temporary credentials."
  read -p "MFA code: " mfa_code
  get_temp_credentials "$mfa_code"
  read -p "Docker Image Name: (press Enter for default: <${DEFAULT_DOCKER_IMAGE_ID}>): " DOCKER_IMAGE_ID
  # If the user pressed Enter, use the default value
  if [ -z "$DOCKER_IMAGE_ID_INPUT" ]; then
    DOCKER_IMAGE_ID="$DEFAULT_DOCKER_IMAGE_ID"
  else      
    DOCKER_IMAGE_ID="$DOCKER_IMAGE_ID"
    fi
  read -p "Docker Image Version: " DOCKER_IMAGE_VERSION
else
  # Use the provided argument if it exists
  get_temp_credentials "$1"
  read -p "Docker Image Name: " DOCKER_IMAGE_ID
  read -p "Docker Image Version: " DOCKER_IMAGE_VERSION
fi

# Your MFA
ecr_login
docker_push

# Next Step: Go into ec2 and pull from ECR

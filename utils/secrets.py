"""
Google Cloud Secret Manager utilities for secure configuration management.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from google.cloud import secretmanager

logger = logging.getLogger(__name__)

def get_secret(secret_name: str, version: str = "latest") -> Optional[str]:
    """
    Retrieve a secret from Google Cloud Secret Manager.
    
    Args:
        secret_name: Name of the secret
        version: Version of the secret (default: "latest")
        
    Returns:
        Secret value as string, or None if not found/error
    """
    try:
        # Get project ID from environment
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            logger.error("GOOGLE_CLOUD_PROJECT environment variable not set")
            return None
        
        # Create the Secret Manager client
        client = secretmanager.SecretManagerServiceClient()
        
        # Build the resource name of the secret version
        name = f"projects/{project_id}/secrets/{secret_name}/versions/{version}"
        
        # Access the secret version
        response = client.access_secret_version(request={"name": name})
        
        # Return the decoded payload
        secret_value = response.payload.data.decode("UTF-8")
        logger.debug(f"Successfully retrieved secret: {secret_name}")
        return secret_value
        
    except Exception as e:
        logger.error(f"Error retrieving secret {secret_name}: {e}")
        return None

def load_firebase_config_from_secrets() -> Dict[str, Any]:
    """
    Load Firebase web configuration from Google Cloud Secret Manager.
    
    Returns:
        Firebase configuration dictionary
    """
    logger.info("Loading Firebase configuration from Secret Manager...")
    
    try:
        # Option 1: Try to get the complete config as a single JSON secret
        complete_config = get_secret("firebase-web-config")
        if complete_config:
            try:
                config = json.loads(complete_config)
                logger.info("Successfully loaded Firebase config from complete secret")
                return config
            except json.JSONDecodeError as e:
                logger.warning(f"Error parsing complete Firebase config JSON: {e}")
        
        # Option 2: Get individual config values
        config = {
            "apiKey": get_secret("firebase-api-key"),
            "authDomain": get_secret("firebase-auth-domain"),
            "projectId": os.getenv("GOOGLE_CLOUD_PROJECT"),  # Use project ID from environment
            "storageBucket": get_secret("firebase-storage-bucket"),
            "messagingSenderId": get_secret("firebase-messaging-sender-id"),
            "appId": get_secret("firebase-app-id")
        }
        
        # Check if all required fields are present
        missing_fields = [k for k, v in config.items() if not v]
        if missing_fields:
            logger.warning(f"Missing Firebase config fields from Secret Manager: {missing_fields}")
            return {}
        
        logger.info("Successfully loaded Firebase config from individual secrets")
        return config
        
    except Exception as e:
        logger.error(f"Error loading Firebase config from Secret Manager: {e}")
        return {}

def update_secret(secret_name: str, secret_value: str) -> bool:
    """
    Update a secret in Google Cloud Secret Manager.
    
    Args:
        secret_name: Name of the secret
        secret_value: New value for the secret
        
    Returns:
        True if successful, False otherwise
    """
    try:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            logger.error("GOOGLE_CLOUD_PROJECT environment variable not set")
            return False
        
        # Create the Secret Manager client
        client = secretmanager.SecretManagerServiceClient()
        
        # Build the resource name of the secret
        parent = f"projects/{project_id}/secrets/{secret_name}"
        
        # Add the secret version
        response = client.add_secret_version(
            request={
                "parent": parent,
                "payload": {"data": secret_value.encode("UTF-8")},
            }
        )
        
        logger.info(f"Successfully updated secret {secret_name}: {response.name}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating secret {secret_name}: {e}")
        return False 
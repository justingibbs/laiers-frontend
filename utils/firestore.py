from google.cloud import firestore
from datetime import datetime
from typing import Optional, Dict, Any
import logging
import os
import json

logger = logging.getLogger(__name__)

class FirestoreService:
    def __init__(self):
        # Load project ID from web config
        try:
            with open("config/firebase-web-config.json", "r") as f:
                web_config = json.load(f)
                project_id = web_config.get('projectId')
                logger.debug(f"Loaded project ID from web config: {project_id}")
        except Exception as e:
            logger.error(f"Failed to load web config: {e}")
            raise

        if not project_id:
            logger.error("Project ID not found in web config")
            raise ValueError("Project ID not found in web config")

        try:
            self.db = firestore.Client(project=project_id)
            logger.info(f"Successfully initialized Firestore client for project: {project_id}")
            self.users_collection = self.db.collection('users')
        except Exception as e:
            logger.error(f"Failed to initialize Firestore client: {e}")
            raise
    
    async def create_user_profile(self, user_id: str, email: str, user_type: str) -> bool:
        """Create a new user profile in Firestore"""
        try:
            user_data = {
                'email': email,
                'user_type': user_type,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'is_active': True,
                'profile': {
                    'name': None,
                    'company': None if user_type == 'talent' else '',
                    'skills': [] if user_type == 'talent' else None,
                    'experience_level': None if user_type == 'talent' else None,
                    'bio': None,
                    'location': None,
                    'preferences': {
                        'job_types': [] if user_type == 'talent' else None,
                        'remote_ok': None if user_type == 'talent' else None,
                        'salary_range': None if user_type == 'talent' else None,
                    }
                }
            }
            
            self.users_collection.document(user_id).set(user_data)
            logger.info(f"Created user profile for {email} ({user_type})")
            return True
            
        except Exception as e:
            logger.error(f"Error creating user profile: {e}")
            return False
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user's profile from Firestore"""
        try:
            doc = self.users_collection.document(user_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """Update a user's profile in Firestore"""
        try:
            # Add updated_at timestamp
            profile_data['updated_at'] = datetime.utcnow()
            
            # Update the document
            self.users_collection.document(user_id).update(profile_data)
            logger.info(f"Updated user profile for {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return False
    
    async def delete_user_profile(self, user_id: str) -> bool:
        """Delete a user's profile from Firestore"""
        try:
            self.users_collection.document(user_id).delete()
            logger.info(f"Deleted user profile for {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting user profile: {e}")
            return False

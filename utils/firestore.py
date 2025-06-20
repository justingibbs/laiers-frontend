from google.cloud import firestore
from datetime import datetime
from typing import Optional, Dict, Any
import logging
import os
import json

logger = logging.getLogger(__name__)

# Define predefined company list
AVAILABLE_COMPANIES = [
    {"id": "company_1", "name": "Company_1", "description": "Leading tech company focused on innovation"},
    {"id": "company_2", "name": "Company_2", "description": "Global consulting and services firm"},
    {"id": "company_3", "name": "Company_3", "description": "Fast-growing startup in fintech space"}
]

class FirestoreService:
    def __init__(self):
        # Load project ID from web config or environment variable
        project_id = None
        
        # Try environment variable first (for production)
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        
        # Fallback to web config file (for development)
        if not project_id:
            try:
                with open("config/firebase-web-config.json", "r") as f:
                    web_config = json.load(f)
                    project_id = web_config.get('projectId')
                    logger.debug(f"Loaded project ID from web config: {project_id}")
            except FileNotFoundError:
                logger.warning("firebase-web-config.json not found")
            except Exception as e:
                logger.error(f"Failed to load web config: {e}")

        if not project_id:
            logger.error("Project ID not found in environment variable GOOGLE_CLOUD_PROJECT or web config")
            raise ValueError("Project ID not found. Set GOOGLE_CLOUD_PROJECT environment variable.")

        try:
            self.db = firestore.Client(project=project_id)
            logger.info(f"Successfully initialized Firestore client for project: {project_id}")
            self.users_collection = self.db.collection('users')
        except Exception as e:
            logger.error(f"Failed to initialize Firestore client: {e}")
            raise
    
    async def create_user_profile(self, user_id: str, email: str, user_type: str, company_id: str = None) -> bool:
        """Create a new user profile in Firestore"""
        try:
            # For company users, validate the company_id
            selected_company = None
            if user_type == 'company':
                if not company_id:
                    logger.error("Company ID required for company type users")
                    return False
                
                # Find the company in our predefined list
                selected_company = next((company for company in AVAILABLE_COMPANIES if company["id"] == company_id), None)
                if not selected_company:
                    logger.error(f"Invalid company ID: {company_id}")
                    return False
            
            user_data = {
                'email': email,
                'user_type': user_type,
                'company_id': company_id if user_type == 'company' else None,
                'company_name': selected_company["name"] if selected_company else None,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'is_active': True,
                'profile': {
                    'name': None,
                    'company': selected_company["name"] if selected_company else (None if user_type == 'talent' else ''),
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

    async def get_company_info(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get company information by ID"""
        try:
            company = next((company for company in AVAILABLE_COMPANIES if company["id"] == company_id), None)
            if company:
                # Get all users from this company
                company_users = []
                users_query = self.users_collection.where('company_id', '==', company_id).stream()
                for user_doc in users_query:
                    user_data = user_doc.to_dict()
                    company_users.append({
                        'id': user_doc.id,
                        'email': user_data.get('email'),
                        'profile': user_data.get('profile', {})
                    })
                
                return {
                    **company,
                    'users': company_users,
                    'user_count': len(company_users)
                }
            return None
        except Exception as e:
            logger.error(f"Error getting company info: {e}")
            return None

    def get_available_companies(self) -> list:
        """Get list of available companies"""
        return AVAILABLE_COMPANIES

    # Opportunity Management Methods
    async def create_opportunity(self, opportunity_data: Dict[str, Any]) -> Optional[str]:
        """Create a new opportunity in Firestore"""
        try:
            # Add timestamp
            opportunity_data['created_at'] = datetime.utcnow()
            opportunity_data['updated_at'] = datetime.utcnow()
            opportunity_data['status'] = 'active'
            
            # Create the opportunity document
            doc_ref = self.db.collection('opportunities').document()
            doc_ref.set(opportunity_data)
            
            logger.info(f"Created opportunity: {doc_ref.id} for company: {opportunity_data.get('company_id')}")
            return doc_ref.id
            
        except Exception as e:
            logger.error(f"Error creating opportunity: {e}")
            return None

    async def get_opportunities_by_company(self, company_id: str) -> list:
        """Get all opportunities for a specific company"""
        try:
            # Simplified query without order_by to avoid index requirement
            query = self.db.collection('opportunities').where('company_id', '==', company_id).where('status', '==', 'active')
            docs = query.stream()
            opportunities = []
            for doc in docs:
                opportunity_data = doc.to_dict()
                opportunity_data['id'] = doc.id
                opportunities.append(opportunity_data)
            
            # Sort by created_at in Python (newest first)
            opportunities.sort(key=lambda x: x.get('created_at'), reverse=True)
            
            logger.info(f"Retrieved {len(opportunities)} opportunities for company: {company_id}")
            return opportunities
        except Exception as e:
            logger.error(f"Error getting opportunities for company {company_id}: {e}")
            return []

    async def get_all_opportunities(self) -> list:
        """Get all active opportunities across all companies"""
        try:
            query = self.db.collection('opportunities').where('status', '==', 'active')
            docs = query.stream()
            opportunities = []
            for doc in docs:
                opportunity_data = doc.to_dict()
                opportunity_data['id'] = doc.id
                opportunities.append(opportunity_data)
            
            # Sort by created_at in Python (newest first)
            opportunities.sort(key=lambda x: x.get('created_at'), reverse=True)
            
            logger.info(f"Retrieved {len(opportunities)} total active opportunities")
            return opportunities
        except Exception as e:
            logger.error(f"Error getting all opportunities: {e}")
            return []

    async def get_opportunity(self, opportunity_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific opportunity by ID"""
        try:
            doc = self.db.collection('opportunities').document(opportunity_id).get()
            if doc.exists:
                opportunity_data = doc.to_dict()
                opportunity_data['id'] = doc.id
                return opportunity_data
            return None
        except Exception as e:
            logger.error(f"Error getting opportunity {opportunity_id}: {e}")
            return None

    async def submit_application(self, application_data: Dict[str, Any]) -> Optional[str]:
        """Submit an application for an opportunity"""
        try:
            # Add timestamp
            application_data['applied_at'] = datetime.utcnow()
            
            # Create the application document
            doc_ref = self.db.collection('applications').document()
            doc_ref.set(application_data)
            
            logger.info(f"Created application: {doc_ref.id} for opportunity: {application_data.get('opportunity_id')}")
            return doc_ref.id
            
        except Exception as e:
            logger.error(f"Error creating application: {e}")
            return None

    async def get_applications_by_opportunity(self, opportunity_id: str) -> list:
        """Get all applications for a specific opportunity"""
        try:
            applications = []
            query = self.db.collection('applications').where('opportunity_id', '==', opportunity_id).order_by('applied_at', direction=firestore.Query.DESCENDING)
            
            for doc in query.stream():
                application_data = doc.to_dict()
                application_data['id'] = doc.id
                applications.append(application_data)
            
            logger.info(f"Retrieved {len(applications)} applications for opportunity: {opportunity_id}")
            return applications
            
        except Exception as e:
            logger.error(f"Error getting applications for opportunity {opportunity_id}: {e}")
            return []

    async def check_existing_application(self, opportunity_id: str, applicant_id: str) -> bool:
        """Check if user has already applied to this opportunity"""
        try:
            query = self.db.collection('applications').where('opportunity_id', '==', opportunity_id).where('applicant_id', '==', applicant_id).limit(1)
            docs = list(query.stream())
            return len(docs) > 0
        except Exception as e:
            logger.error(f"Error checking existing application: {e}")
            return False

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import logging
import json

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("Supabase package not installed. Database features will be disabled.")

class DatabaseManager:
    def __init__(self):
        if not SUPABASE_AVAILABLE:
            logger.warning("Supabase package not available. Database operations will be skipped.")
            self.supabase = None
            return

        supabase_url = os.getenv('VITE_SUPABASE_URL')
        supabase_key = os.getenv('VITE_SUPABASE_ANON_KEY')

        if not supabase_url or not supabase_key:
            logger.warning("Supabase credentials not found. Database operations will be skipped.")
            self.supabase = None
        else:
            try:
                self.supabase = create_client(supabase_url, supabase_key)
                logger.info("Connected to Supabase successfully")
            except Exception as e:
                logger.error(f"Failed to connect to Supabase: {e}")
                self.supabase = None

    def create_session(self, file_name: str, file_type: str) -> Optional[str]:
        if not self.supabase:
            logger.warning("Supabase not available, skipping session creation")
            return None

        try:
            data = {
                'file_name': file_name,
                'file_type': file_type,
                'status': 'processing'
            }

            result = self.supabase.table('ocr_sessions').insert(data).execute()

            if result.data and len(result.data) > 0:
                session_id = result.data[0]['id']
                logger.info(f"Created OCR session: {session_id}")
                return session_id
            return None
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return None

    def update_session(
        self,
        session_id: str,
        status: str,
        error_message: Optional[str] = None,
        processing_time_ms: Optional[int] = None,
        overall_confidence: Optional[float] = None
    ):
        if not self.supabase or not session_id:
            return

        try:
            data = {'status': status}
            if error_message:
                data['error_message'] = error_message
            if processing_time_ms is not None:
                data['processing_time_ms'] = processing_time_ms
            if overall_confidence is not None:
                data['overall_confidence'] = overall_confidence

            self.supabase.table('ocr_sessions').update(data).eq('id', session_id).execute()
            logger.info(f"Updated session {session_id}: status={status}")
        except Exception as e:
            logger.error(f"Failed to update session: {e}")

    def save_extracted_license(
        self,
        session_id: Optional[str],
        normalized_data: Dict[str, Any],
        raw_ocr_text: str,
        validation_report: Dict[str, Any]
    ) -> Optional[str]:
        if not self.supabase:
            logger.warning("Supabase not available, skipping license save")
            return None

        try:
            confidence_scores = normalized_data.pop('confidence', {})

            data = {
                'session_id': session_id,
                'first_name': normalized_data.get('first_name'),
                'last_name': normalized_data.get('last_name'),
                'license_number': normalized_data.get('license_number'),
                'date_of_birth': normalized_data.get('date_of_birth'),
                'expiration_date': normalized_data.get('expiration_date'),
                'street_address': normalized_data.get('street_address'),
                'city': normalized_data.get('city'),
                'state': normalized_data.get('state'),
                'zip_code': normalized_data.get('zip_code'),
                'sex': normalized_data.get('sex'),
                'confidence_scores': json.dumps(confidence_scores),
                'raw_ocr_text': raw_ocr_text,
                'validation_report': json.dumps(validation_report)
            }

            result = self.supabase.table('extracted_licenses').insert(data).execute()

            if result.data and len(result.data) > 0:
                license_id = result.data[0]['id']
                logger.info(f"Saved extracted license: {license_id}")
                return license_id
            return None
        except Exception as e:
            logger.error(f"Failed to save extracted license: {e}")
            return None

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        if not self.supabase or not session_id:
            return None

        try:
            result = self.supabase.table('ocr_sessions').select('*').eq('id', session_id).maybeSingle().execute()
            return result.data
        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return None

    def get_extracted_license(self, session_id: str) -> Optional[Dict[str, Any]]:
        if not self.supabase or not session_id:
            return None

        try:
            result = self.supabase.table('extracted_licenses').select('*').eq('session_id', session_id).maybeSingle().execute()
            return result.data
        except Exception as e:
            logger.error(f"Failed to get extracted license: {e}")
            return None

    def search_by_license_number(self, license_number: str) -> Optional[list]:
        if not self.supabase:
            return None

        try:
            result = self.supabase.table('extracted_licenses').select('*').eq('license_number', license_number).execute()
            return result.data
        except Exception as e:
            logger.error(f"Failed to search by license number: {e}")
            return None

    def get_recent_sessions(self, limit: int = 10) -> Optional[list]:
        if not self.supabase:
            return None

        try:
            result = self.supabase.table('ocr_sessions').select('*').order('created_at', desc=True).limit(limit).execute()
            return result.data
        except Exception as e:
            logger.error(f"Failed to get recent sessions: {e}")
            return None

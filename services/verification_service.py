import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging
import hmac
import base64

logger = logging.getLogger(__name__)

class DocumentVerificationError(Exception):
    """Custom exception for document verification errors."""
    pass

class DocumentVerificationService:
    # Time window for timestamp verification (in minutes)
    TIMESTAMP_WINDOW = 5
    
    @staticmethod
    def calculate_document_hash(content: str) -> str:
        """Calculate SHA-256 hash of document content."""
        if not content:
            raise DocumentVerificationError("Document content cannot be empty")
        try:
            return hashlib.sha256(content.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error calculating document hash: {str(e)}")
            raise DocumentVerificationError("Failed to calculate document hash")
    
    @staticmethod
    def verify_signatures(signature1: str, signature2: str) -> Tuple[bool, str]:
        """Verify if both signatures are present and valid."""
        try:
            if not signature1 or not signature2:
                return False, "Missing signatures"
                
            if not (signature1.startswith('data:image') and signature2.startswith('data:image')):
                return False, "Invalid signature format"
                
            # Verify signature data integrity
            try:
                sig1_data = signature1.split(',')[1]
                sig2_data = signature2.split(',')[1]
                base64.b64decode(sig1_data)
                base64.b64decode(sig2_data)
            except:
                return False, "Corrupted signature data"
                
            return True, "Signatures valid"
        except Exception as e:
            logger.error(f"Error verifying signatures: {str(e)}")
            raise DocumentVerificationError("Failed to verify signatures")
    
    @staticmethod
    def create_verification_record(agreement_id: int, content: str) -> Dict:
        """Create a verification record for the agreement."""
        if not content:
            raise DocumentVerificationError("Document content cannot be empty")
            
        try:
            timestamp = datetime.utcnow()
            content_hash = DocumentVerificationService.calculate_document_hash(content)
            
            # Prepare blockchain record structure
            blockchain_data = {
                'agreement_id': agreement_id,
                'content_hash': content_hash,
                'timestamp': timestamp.isoformat()
            }
            
            return {
                'agreement_id': agreement_id,
                'content_hash': content_hash,
                'timestamp': timestamp.isoformat(),
                'status': 'created',
                'blockchain_data': blockchain_data
            }
        except Exception as e:
            logger.error(f"Error creating verification record: {str(e)}")
            raise DocumentVerificationError("Failed to create verification record")
    
    @staticmethod
    def verify_timestamp(timestamp_str: str) -> Tuple[bool, str]:
        """Verify if the timestamp is within acceptable range."""
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            now = datetime.utcnow()
            time_diff = abs((now - timestamp).total_seconds() / 60)
            
            if time_diff > DocumentVerificationService.TIMESTAMP_WINDOW:
                return False, f"Timestamp verification failed: outside {DocumentVerificationService.TIMESTAMP_WINDOW} minute window"
            return True, "Timestamp verified"
        except Exception as e:
            return False, f"Invalid timestamp format: {str(e)}"
    
    @staticmethod
    def verify_document_integrity(stored_hash: str, current_content: str) -> Tuple[bool, str]:
        """Verify if document content hasn't been tampered with."""
        if not stored_hash or not current_content:
            raise DocumentVerificationError("Missing hash or content for verification")
            
        try:
            current_hash = DocumentVerificationService.calculate_document_hash(current_content)
            if stored_hash == current_hash:
                return True, "Document integrity verified"
            return False, "Document content has been modified"
        except Exception as e:
            logger.error(f"Error verifying document integrity: {str(e)}")
            raise DocumentVerificationError("Failed to verify document integrity")
    
    @staticmethod
    def generate_verification_code(agreement_id: int, content_hash: str) -> str:
        """Generate a unique verification code for the agreement."""
        if not agreement_id or not content_hash:
            raise DocumentVerificationError("Missing required data for verification code generation")
            
        try:
            timestamp = datetime.utcnow().isoformat()
            unique_string = f"{agreement_id}-{content_hash}-{timestamp}"
            return hashlib.sha256(unique_string.encode()).hexdigest()[:12]
        except Exception as e:
            logger.error(f"Error generating verification code: {str(e)}")
            raise DocumentVerificationError("Failed to generate verification code")
    
    @staticmethod
    def verify_agreement(agreement, stored_verification: Dict) -> Tuple[bool, Dict]:
        """Verify the entire agreement including content, signatures, and timestamps."""
        verification_results = {
            'is_valid': False,
            'content_integrity': {'status': False, 'message': ''},
            'signatures': {'status': False, 'message': ''},
            'timestamp': {'status': False, 'message': ''},
            'overall_message': ''
        }

        try:
            if not agreement or not stored_verification:
                verification_results['overall_message'] = "Agreement or verification record not found"
                return False, verification_results
            
            # Check content integrity
            content_valid, content_msg = DocumentVerificationService.verify_document_integrity(
                stored_verification.get('content_hash'),
                agreement.content
            )
            verification_results['content_integrity'] = {
                'status': content_valid,
                'message': content_msg
            }
            
            # Check timestamp
            time_valid, time_msg = DocumentVerificationService.verify_timestamp(
                stored_verification.get('timestamp')
            )
            verification_results['timestamp'] = {
                'status': time_valid,
                'message': time_msg
            }
            
            # Check signatures if agreement is signed
            if agreement.signed_at:
                sig_valid, sig_msg = DocumentVerificationService.verify_signatures(
                    agreement.signature1,
                    agreement.signature2
                )
                verification_results['signatures'] = {
                    'status': sig_valid,
                    'message': sig_msg
                }
            else:
                verification_results['signatures'] = {
                    'status': None,
                    'message': 'Agreement not yet signed'
                }
            
            # Overall verification status
            is_valid = (content_valid and time_valid and 
                       (not agreement.signed_at or verification_results['signatures']['status']))
            
            verification_results['is_valid'] = is_valid
            verification_results['overall_message'] = (
                "Document verification successful" if is_valid
                else "Document verification failed"
            )
            
            return is_valid, verification_results
            
        except Exception as e:
            logger.error(f"Error verifying agreement: {str(e)}")
            verification_results['overall_message'] = f"An error occurred during verification: {str(e)}"
            return False, verification_results

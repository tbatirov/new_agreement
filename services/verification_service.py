import hashlib
import json
from datetime import datetime
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class DocumentVerificationError(Exception):
    """Custom exception for document verification errors."""
    pass

class DocumentVerificationService:
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
    def verify_signatures(signature1: str, signature2: str) -> bool:
        """Verify if both signatures are present and valid."""
        try:
            return bool(signature1 and signature2 and 
                       signature1.startswith('data:image') and 
                       signature2.startswith('data:image'))
        except Exception as e:
            logger.error(f"Error verifying signatures: {str(e)}")
            raise DocumentVerificationError("Failed to verify signatures")
    
    @staticmethod
    def create_verification_record(agreement_id: int, content: str) -> Dict:
        """Create a verification record for the agreement."""
        if not content:
            raise DocumentVerificationError("Document content cannot be empty")
            
        try:
            return {
                'agreement_id': agreement_id,
                'content_hash': DocumentVerificationService.calculate_document_hash(content),
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'created'
            }
        except Exception as e:
            logger.error(f"Error creating verification record: {str(e)}")
            raise DocumentVerificationError("Failed to create verification record")
    
    @staticmethod
    def verify_document_integrity(stored_hash: str, current_content: str) -> bool:
        """Verify if document content hasn't been tampered with."""
        if not stored_hash or not current_content:
            raise DocumentVerificationError("Missing hash or content for verification")
            
        try:
            current_hash = DocumentVerificationService.calculate_document_hash(current_content)
            return stored_hash == current_hash
        except Exception as e:
            logger.error(f"Error verifying document integrity: {str(e)}")
            raise DocumentVerificationError("Failed to verify document integrity")
    
    @staticmethod
    def generate_verification_code(agreement_id: int, content_hash: str) -> str:
        """Generate a unique verification code for the agreement."""
        if not agreement_id or not content_hash:
            raise DocumentVerificationError("Missing required data for verification code generation")
            
        try:
            unique_string = f"{agreement_id}-{content_hash}-{datetime.utcnow().isoformat()}"
            return hashlib.sha256(unique_string.encode()).hexdigest()[:12]
        except Exception as e:
            logger.error(f"Error generating verification code: {str(e)}")
            raise DocumentVerificationError("Failed to generate verification code")
    
    @staticmethod
    def verify_agreement(agreement, stored_verification: Dict) -> Tuple[bool, str]:
        """Verify the entire agreement including content and signatures."""
        try:
            if not agreement or not stored_verification:
                return False, "Agreement or verification record not found"
                
            # Check content integrity
            try:
                if not DocumentVerificationService.verify_document_integrity(
                    stored_verification.get('content_hash'), 
                    agreement.content
                ):
                    return False, "Document content has been modified"
            except DocumentVerificationError as e:
                return False, str(e)
                
            # Check signatures if agreement is signed
            if agreement.signed_at:
                try:
                    if not DocumentVerificationService.verify_signatures(
                        agreement.signature1, 
                        agreement.signature2
                    ):
                        return False, "Invalid signatures"
                except DocumentVerificationError as e:
                    return False, str(e)
                    
            return True, "Document verification successful"
            
        except Exception as e:
            logger.error(f"Error verifying agreement: {str(e)}")
            return False, "An error occurred during verification"

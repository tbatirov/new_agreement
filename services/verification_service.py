import hashlib
import json
from datetime import datetime
from typing import Dict, Optional, Tuple

class DocumentVerificationService:
    @staticmethod
    def calculate_document_hash(content: str) -> str:
        """Calculate SHA-256 hash of document content."""
        return hashlib.sha256(content.encode()).hexdigest()
    
    @staticmethod
    def verify_signatures(signature1: str, signature2: str) -> bool:
        """Verify if both signatures are present and valid."""
        return bool(signature1 and signature2 and 
                   signature1.startswith('data:image') and 
                   signature2.startswith('data:image'))
    
    @staticmethod
    def create_verification_record(agreement_id: int, content: str) -> Dict:
        """Create a verification record for the agreement."""
        return {
            'agreement_id': agreement_id,
            'content_hash': DocumentVerificationService.calculate_document_hash(content),
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'created'
        }
    
    @staticmethod
    def verify_document_integrity(stored_hash: str, current_content: str) -> bool:
        """Verify if document content hasn't been tampered with."""
        current_hash = DocumentVerificationService.calculate_document_hash(current_content)
        return stored_hash == current_hash
    
    @staticmethod
    def generate_verification_code(agreement_id: int, content_hash: str) -> str:
        """Generate a unique verification code for the agreement."""
        unique_string = f"{agreement_id}-{content_hash}-{datetime.utcnow().isoformat()}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:12]
    
    @staticmethod
    def verify_agreement(agreement, stored_verification: Dict) -> Tuple[bool, str]:
        """Verify the entire agreement including content and signatures."""
        if not agreement or not stored_verification:
            return False, "Agreement or verification record not found"
            
        # Check content integrity
        if not DocumentVerificationService.verify_document_integrity(
            stored_verification['content_hash'], 
            agreement.content
        ):
            return False, "Document content has been modified"
            
        # Check signatures if agreement is signed
        if agreement.signed_at:
            if not DocumentVerificationService.verify_signatures(
                agreement.signature1, 
                agreement.signature2
            ):
                return False, "Invalid signatures"
                
        return True, "Document verification successful"

import qrcode
from io import BytesIO
import base64
from pyzbar.pyzbar import decode
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class QRCodeService:
    @staticmethod
    def generate_verification_qr(verification_code: str, agreement_id: int) -> str:
        """Generate a QR code for agreement verification."""
        try:
            # Create QR code instance
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            
            # Add verification data
            verification_url = f"/verify/{verification_code}"
            qr.add_data(verification_url)
            qr.make(fit=True)

            # Create an image from the QR Code
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64 for embedding in HTML
            buffered = BytesIO()
            qr_image.save(buffered, format="PNG")
            qr_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            return f"data:image/png;base64,{qr_base64}"
        except Exception as e:
            logger.error(f"Error generating QR code: {str(e)}")
            return None

    @staticmethod
    def scan_qr_code(image_data: str) -> str:
        """Scan QR code from image data."""
        try:
            # Remove data URL prefix if present
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
                
            # Convert base64 to image
            image_bytes = base64.b64decode(image_data)
            image = Image.open(BytesIO(image_bytes))
            
            # Decode QR code
            decoded_objects = decode(image)
            if decoded_objects:
                return decoded_objects[0].data.decode()
            return None
        except Exception as e:
            logger.error(f"Error scanning QR code: {str(e)}")
            return None

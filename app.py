import os
import logging
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, g, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_babel import Babel, gettext as _, refresh
import pdfkit
from datetime import datetime
from templates import AGREEMENT_TEMPLATES
from services.ai_service import get_template_suggestions, analyze_and_format_text, highlight_key_elements
from services.verification_service import DocumentVerificationService
from services.qr_service import QRCodeService
import io
import json
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'
app.config['LANGUAGES'] = {
    'en': 'English',
    'es': 'Español',
    'fr': 'Français',
    'de': 'Deutsch',
    'zh': '中文'
}

class Agreement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    signature1 = db.Column(db.Text)
    signature2 = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    signed_at = db.Column(db.DateTime)
    verification_data = db.Column(db.Text)  # JSON string containing verification info
    verification_code = db.Column(db.String(12), unique=True)
    last_verified_at = db.Column(db.DateTime)

def get_locale():
    if 'lang_code' in session:
        return session.get('lang_code')
    
    if not g.get('lang_code', None):
        preferred = request.accept_languages.best_match(app.config['LANGUAGES'].keys())
        g.lang_code = preferred or app.config['BABEL_DEFAULT_LOCALE']
        session['lang_code'] = g.lang_code
    
    return g.lang_code

babel = Babel(app, locale_selector=get_locale)
db.init_app(app)

@app.route('/language/<lang_code>')
def set_language(lang_code):
    if lang_code not in app.config['LANGUAGES']:
        flash(_('Invalid language selected'), 'error')
        return redirect(request.referrer or url_for('index'))
    
    session['lang_code'] = lang_code
    g.lang_code = lang_code
    refresh()
    
    flash(_('Language changed to %(language)s', language=app.config['LANGUAGES'][lang_code]), 'success')
    return redirect(request.referrer or url_for('index'))

@app.before_request
def before_request():
    g.lang_code = get_locale()
    g.languages = app.config['LANGUAGES']

with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/templates')
def get_templates():
    """Get all available templates."""
    try:
        templates = [{"id": key, "name": _(template["name"])} for key, template in AGREEMENT_TEMPLATES.items()]
        logger.info(f"Successfully retrieved {len(templates)} templates")
        return jsonify(templates)
    except Exception as e:
        logger.error(f"Error retrieving templates: {str(e)}")
        return jsonify({"error": _("Could not retrieve templates")}), 500

@app.route('/templates/<template_id>')
def get_template_content(template_id):
    """Get content for a specific template."""
    try:
        template = AGREEMENT_TEMPLATES.get(template_id)
        if not template:
            logger.warning(f"Template not found: {template_id}")
            return jsonify({"error": _("Template not found")}), 404
            
        logger.info(f"Successfully retrieved template: {template_id}")
        return jsonify({"content": _(template["content"])})
    except Exception as e:
        logger.error(f"Error retrieving template content: {str(e)}")
        return jsonify({"error": _("Could not retrieve template content")}), 500

@app.route('/analyze-text', methods=['POST'])
def analyze_text():
    """Analyze agreement text."""
    try:
        text = request.get_json()
        if not text or 'content' not in text:
            return jsonify({"error": _("No content provided")}), 400
            
        analysis = analyze_and_format_text(text['content'])
        if analysis:
            highlights = highlight_key_elements(text['content'])
            analysis['highlights'] = highlights
            logger.info("Successfully analyzed text")
            return jsonify(analysis)
            
        logger.error("Text analysis returned no results")
        return jsonify({"error": _("Could not analyze text")}), 500
    except Exception as e:
        logger.error(f"Error analyzing text: {str(e)}")
        return jsonify({"error": _("Error analyzing text")}), 500

@app.route('/suggest-template', methods=['POST'])
def suggest_template():
    """Get template suggestions based on content."""
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({"error": _("No content provided")}), 400
            
        suggestion = get_template_suggestions(data['content'])
        if suggestion:
            logger.info("Successfully generated template suggestions")
            return jsonify(suggestion)
            
        logger.error("No template suggestions generated")
        return jsonify({"error": _("Could not generate suggestion")}), 500
    except Exception as e:
        logger.error(f"Error generating template suggestions: {str(e)}")
        return jsonify({"error": _("Error generating suggestions")}), 500

@app.route('/create', methods=['GET', 'POST'])
def create_agreement():
    if request.method == 'POST':
        content = request.form.get('content')
        if not content:
            flash(_('Agreement content is required'), 'error')
            return redirect(url_for('create_agreement'))
        
        try:
            # Start database transaction
            agreement = Agreement(content=content)
            db.session.add(agreement)
            db.session.flush()  # Get the ID without committing
            
            # Create verification record with the agreement ID
            try:
                verification_data = DocumentVerificationService.create_verification_record(
                    agreement_id=agreement.id,
                    content=content
                )
                agreement.verification_data = json.dumps(verification_data)
                
                # Generate verification code
                try:
                    agreement.verification_code = DocumentVerificationService.generate_verification_code(
                        agreement.id,
                        verification_data['content_hash']
                    )
                except Exception as e:
                    logger.error(f"Error generating verification code: {str(e)}")
                    raise ValueError("Failed to generate verification code")
                
                # Commit the transaction
                db.session.commit()
                logger.info(f"Agreement created successfully with ID: {agreement.id}")
                
                flash(_('Agreement created successfully'), 'success')
                return redirect(url_for('sign_agreement', id=agreement.id))
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error creating verification record: {str(e)}")
                flash(_('Error creating verification record'), 'error')
                return redirect(url_for('create_agreement'))
                
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error: {str(e)}")
            flash(_('Error saving agreement'), 'error')
            return redirect(url_for('create_agreement'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Unexpected error: {str(e)}")
            flash(_('An unexpected error occurred'), 'error')
            return redirect(url_for('create_agreement'))
            
    return render_template('create_agreement.html')

@app.route('/verify/<verification_code>')
def verify_agreement_by_code(verification_code):
    """Verify an agreement using its verification code."""
    try:
        agreement = Agreement.query.filter_by(verification_code=verification_code).first_or_404()
        verification_data = json.loads(agreement.verification_data)
        
        # Get detailed verification results
        is_valid, verification_results = DocumentVerificationService.verify_agreement(
            agreement, 
            verification_data
        )
        
        # Generate QR code for sharing
        qr_code = QRCodeService.generate_verification_qr(
            verification_code,
            agreement.id
        )
        
        # Update last verified timestamp
        agreement.last_verified_at = datetime.utcnow()
        db.session.commit()
        
        return render_template(
            'verify_agreement.html',
            agreement=agreement,
            verification_results=verification_results,
            verification_data=verification_data,
            qr_code=qr_code
        )
    except Exception as e:
        logger.error(f"Error verifying agreement: {str(e)}")
        flash(_('Error verifying agreement'), 'error')
        return redirect(url_for('index'))

@app.route('/sign/<int:id>', methods=['GET', 'POST'])
def sign_agreement(id):
    try:
        agreement = Agreement.query.get_or_404(id)
        if request.method == 'POST':
            signature1 = request.form.get('signature1')
            signature2 = request.form.get('signature2')
            if not signature1 or not signature2:
                flash(_('Both signatures are required'), 'error')
                return redirect(url_for('sign_agreement', id=id))
            
            try:
                agreement.signature1 = signature1
                agreement.signature2 = signature2
                agreement.signed_at = datetime.utcnow()
                
                verification_data = json.loads(agreement.verification_data)
                verification_data['status'] = 'signed'
                verification_data['signed_at'] = agreement.signed_at.isoformat()
                agreement.verification_data = json.dumps(verification_data)
                
                db.session.commit()
                flash(_('Agreement signed successfully'), 'success')
                return redirect(url_for('view_agreement', id=id))
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error signing agreement: {str(e)}")
                flash(_('Error signing agreement'), 'error')
                return redirect(url_for('sign_agreement', id=id))
                
        return render_template('sign_agreement.html', agreement=agreement)
    except Exception as e:
        logger.error(f"Error accessing agreement: {str(e)}")
        flash(_('Error accessing agreement'), 'error')
        return redirect(url_for('index'))

@app.route('/view/<int:id>')
def view_agreement(id):
    try:
        agreement = Agreement.query.get_or_404(id)
        verification_data = json.loads(agreement.verification_data)
        is_valid, verification_results = DocumentVerificationService.verify_agreement(agreement, verification_data)
        return render_template(
            'view_agreement.html',
            agreement=agreement,
            is_valid=is_valid,
            verification_results=verification_results,
            verification_data=verification_data
        )
    except Exception as e:
        logger.error(f"Error viewing agreement: {str(e)}")
        flash(_('Error viewing agreement'), 'error')
        return redirect(url_for('index'))

@app.route('/download/<int:id>')
def download_agreement(id):
    try:
        agreement = Agreement.query.get_or_404(id)
        html = render_template('view_agreement.html', agreement=agreement)
        pdf = pdfkit.from_string(html, False)
        return send_file(
            io.BytesIO(pdf),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'agreement_{id}.pdf'
        )
    except Exception as e:
        logger.error(f"Error downloading agreement: {str(e)}")
        flash(_('Error downloading agreement'), 'error')
        return redirect(url_for('view_agreement', id=id))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

import os
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, g, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_babel import Babel, gettext as _, refresh
import pdfkit
from datetime import datetime
from templates import AGREEMENT_TEMPLATES
from services.ai_service import get_template_suggestions, analyze_and_format_text, highlight_key_elements
import io

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

def get_locale():
    # First try to get language from session
    if 'lang_code' in session:
        return session.get('lang_code')
    
    # Then try to get it from the request header
    if not g.get('lang_code', None):
        # Get browser's preferred language
        preferred = request.accept_languages.best_match(app.config['LANGUAGES'].keys())
        g.lang_code = preferred or app.config['BABEL_DEFAULT_LOCALE']
        session['lang_code'] = g.lang_code
    
    return g.lang_code

babel = Babel(app, locale_selector=get_locale)
db.init_app(app)

@app.route('/language/<lang_code>')
def set_language(lang_code):
    # Validate language code
    if lang_code not in app.config['LANGUAGES']:
        flash(_('Invalid language selected'), 'error')
        return redirect(request.referrer or url_for('index'))
    
    # Store language preference
    session['lang_code'] = lang_code
    g.lang_code = lang_code
    
    # Refresh translations
    refresh()
    
    # Show success message
    flash(_('Language changed to %(language)s', language=app.config['LANGUAGES'][lang_code]), 'success')
    
    # Redirect back to previous page or home
    return redirect(request.referrer or url_for('index'))

@app.before_request
def before_request():
    g.lang_code = get_locale()
    g.languages = app.config['LANGUAGES']

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/templates')
def get_templates():
    templates = [{"id": key, "name": _(template["name"])} for key, template in AGREEMENT_TEMPLATES.items()]
    return jsonify(templates)

@app.route('/templates/<template_id>')
def get_template_content(template_id):
    template = AGREEMENT_TEMPLATES.get(template_id)
    if template:
        return jsonify({"content": _(template["content"])})
    return jsonify({"error": _("Template not found")}), 404

@app.route('/analyze-text', methods=['POST'])
def analyze_text():
    text = request.get_json()
    if not text or 'content' not in text:
        return jsonify({"error": _("No content provided")}), 400
        
    analysis = analyze_and_format_text(text['content'])
    if analysis:
        highlights = highlight_key_elements(text['content'])
        analysis['highlights'] = highlights
        return jsonify(analysis)
    return jsonify({"error": _("Could not analyze text")}), 500

@app.route('/suggest-template', methods=['POST'])
def suggest_template():
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({"error": _("No content provided")}), 400
        
    suggestion = get_template_suggestions(data['content'])
    if suggestion:
        return jsonify(suggestion)
    return jsonify({"error": _("Could not generate suggestion")}), 500

@app.route('/create', methods=['GET', 'POST'])
def create_agreement():
    if request.method == 'POST':
        content = request.form.get('content')
        if not content:
            flash(_('Agreement content is required'), 'error')
            return redirect(url_for('create_agreement'))
            
        agreement = Agreement(content=content)
        db.session.add(agreement)
        db.session.commit()
        flash(_('Agreement created successfully'), 'success')
        return redirect(url_for('sign_agreement', id=agreement.id))
    return render_template('create_agreement.html')

@app.route('/sign/<int:id>', methods=['GET', 'POST'])
def sign_agreement(id):
    agreement = Agreement.query.get_or_404(id)
    if request.method == 'POST':
        signature1 = request.form.get('signature1')
        signature2 = request.form.get('signature2')
        if not signature1 or not signature2:
            flash(_('Both signatures are required'), 'error')
            return redirect(url_for('sign_agreement', id=id))
            
        agreement.signature1 = signature1
        agreement.signature2 = signature2
        agreement.signed_at = datetime.utcnow()
        db.session.commit()
        flash(_('Agreement signed successfully'), 'success')
        return redirect(url_for('view_agreement', id=id))
    return render_template('sign_agreement.html', agreement=agreement)

@app.route('/view/<int:id>')
def view_agreement(id):
    agreement = Agreement.query.get_or_404(id)
    return render_template('view_agreement.html', agreement=agreement)

@app.route('/download/<int:id>')
def download_agreement(id):
    agreement = Agreement.query.get_or_404(id)
    html = render_template('view_agreement.html', agreement=agreement)
    pdf = pdfkit.from_string(html, False)
    return send_file(
        io.BytesIO(pdf),
        download_name=f'agreement_{id}.pdf',
        mimetype='application/pdf'
    )

import os
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import pdfkit
from datetime import datetime
from templates import AGREEMENT_TEMPLATES
from services.ai_service import get_template_suggestions
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
db.init_app(app)

with app.app_context():
    from models import Agreement
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/templates')
def get_templates():
    templates = [{"id": key, "name": template["name"]} for key, template in AGREEMENT_TEMPLATES.items()]
    return jsonify(templates)

@app.route('/templates/<template_id>')
def get_template_content(template_id):
    template = AGREEMENT_TEMPLATES.get(template_id)
    if template:
        return jsonify({"content": template["content"]})
    return jsonify({"error": "Template not found"}), 404

@app.route('/suggest-template', methods=['POST'])
def suggest_template():
    user_input = request.json.get('content', '')
    if not user_input:
        return jsonify({"error": "No content provided"}), 400
        
    suggestion = get_template_suggestions(user_input)
    if suggestion:
        return jsonify(suggestion)
    return jsonify({"error": "Could not generate suggestion"}), 500

@app.route('/create', methods=['GET', 'POST'])
def create_agreement():
    if request.method == 'POST':
        content = request.form.get('content')
        agreement = Agreement(
            content=content,
            created_at=datetime.utcnow()
        )
        db.session.add(agreement)
        db.session.commit()
        return redirect(url_for('sign_agreement', id=agreement.id))
    return render_template('create_agreement.html')

@app.route('/sign/<int:id>', methods=['GET', 'POST'])
def sign_agreement(id):
    agreement = Agreement.query.get_or_404(id)
    if request.method == 'POST':
        signature1 = request.form.get('signature1')
        signature2 = request.form.get('signature2')
        agreement.signature1 = signature1
        agreement.signature2 = signature2
        agreement.signed_at = datetime.utcnow()
        db.session.commit()
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

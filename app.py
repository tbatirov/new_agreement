import os
from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import pdfkit
from datetime import datetime
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

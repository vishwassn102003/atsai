from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from models import Resume, Payment, db
from utils.resume_parser import extract_text
from utils.ats_engine import calculate_ats_score, improve_resume
from utils.pdf_generator import generate_pdf
import io, hmac, hashlib
from datetime import datetime

# Safe razorpay import — avoids crash if pkg_resources is missing
try:
    import razorpay as razorpay_lib
    RAZORPAY_AVAILABLE = True
except Exception:
    razorpay_lib = None
    RAZORPAY_AVAILABLE = False

api_bp = Blueprint('api', __name__)


# ── ATS Check ────────────────────────────────────────────────────────────────

@api_bp.route('/check-ats', methods=['POST'])
@login_required
def check_ats():
    mode = request.form.get('mode', 'with_jd')
    jd   = request.form.get('job_description', '').strip()
    file = request.files.get('resume')

    if not file:
        return jsonify({'error': 'Please upload your resume file.'}), 400
    if mode == 'with_jd' and not jd:
        return jsonify({'error': 'Please paste the job description.'}), 400

    try:
        resume_text = extract_text(file)
    except Exception as e:
        return jsonify({'error': f'Could not read file: {str(e)}'}), 400

    if not resume_text.strip():
        return jsonify({'error': 'Resume appears empty or unreadable.'}), 400

    try:
        result = calculate_ats_score(
            resume_text=resume_text, job_desc=jd, mode=mode,
            model=current_app.config['GEMINI_MODEL'],
            api_key=current_app.config['GEMINI_API_KEY']
        )
    except Exception as e:
        return jsonify({'error': f'AI error: {str(e)}'}), 500

    resume = Resume(
        user_id=current_user.id, filename=file.filename,
        original_text=resume_text, job_description=jd,
        ats_score=result['score'], mode=mode
    )
    db.session.add(resume)
    db.session.commit()

    return jsonify({
        'success': True, 'resume_id': resume.id,
        'score': result['score'], 'breakdown': result['breakdown'],
        'suggestions': result['suggestions'],
        'missing_keywords': result.get('missing_keywords', []),
    })


# ── AI Improve ────────────────────────────────────────────────────────────────

@api_bp.route('/improve-resume', methods=['POST'])
@login_required
def improve_resume_api():
    if not current_user.can_edit():
        return jsonify({'error': 'No active subscription or edit limit reached.'}), 403

    data      = request.get_json()
    resume_id = data.get('resume_id')
    resume    = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first()
    if not resume:
        return jsonify({'error': 'Resume not found.'}), 404

    try:
        improved = improve_resume(
            resume_text=resume.improved_text or resume.original_text,
            job_desc=resume.job_description, mode=resume.mode,
            model=current_app.config['GEMINI_MODEL'],
            api_key=current_app.config['GEMINI_API_KEY']
        )
    except Exception as e:
        return jsonify({'error': f'AI error: {str(e)}'}), 500

    resume.improved_text  = improved['text']
    resume.improved_score = improved['new_score']
    resume.updated_at     = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'success': True, 'improved': improved['text'],
        'new_score': improved['new_score'],
        'edits_left': current_user.edits_remaining()
    })


# ── Save Manual Edits ─────────────────────────────────────────────────────────

@api_bp.route('/save-resume', methods=['POST'])
@login_required
def save_resume():
    if not current_user.can_edit():
        return jsonify({'error': 'No active subscription or edit limit reached.'}), 403

    data      = request.get_json()
    resume_id = data.get('resume_id')
    content   = data.get('content', '').strip()
    resume    = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first()
    if not resume:
        return jsonify({'error': 'Resume not found.'}), 404

    resume.improved_text = content
    resume.updated_at    = datetime.utcnow()
    db.session.commit()

    return jsonify({'success': True, 'edits_left': current_user.edits_remaining()})


# ── Download PDF (requires paid subscription) ─────────────────────────────────

@api_bp.route('/download-pdf/<int:resume_id>', methods=['GET'])
@login_required
def download_pdf_api(resume_id):
    # PAYMENT GATE — must have active subscription to download
    if not current_user.can_download():
        return jsonify({'error': 'Payment required to download PDF.'}), 402

    resume = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first_or_404()
    text   = resume.improved_text or resume.original_text

    try:
        pdf_bytes = generate_pdf(text, current_user.name or 'Resume')
    except Exception as e:
        return jsonify({'error': f'PDF error: {str(e)}'}), 500

    slug = (current_user.name or 'resume').replace(' ', '_')
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'{slug}_ATS_Resume.pdf'
    )


# ── Create Razorpay Order ─────────────────────────────────────────────────────

@api_bp.route('/create-order', methods=['POST'])
@login_required
def create_order():
    key_id     = current_app.config.get('RAZORPAY_KEY_ID')
    key_secret = current_app.config.get('RAZORPAY_KEY_SECRET')
    resume_id  = (request.get_json() or {}).get('resume_id')

    # Dev mode — no Razorpay keys configured, or razorpay unavailable
    if not key_id or not key_secret or not RAZORPAY_AVAILABLE:
        _activate_dev_subscription(resume_id)
        return jsonify({'dev': True})

    try:
        client = razorpay_lib.Client(auth=(key_id, key_secret))
        order  = client.order.create({
            'amount': current_app.config['PRICE_PAISE'],
            'currency': 'INR',
            'payment_capture': 1
        })
        payment = Payment(
            user_id=current_user.id, resume_id=resume_id,
            razorpay_order=order['id'],
            amount_paise=current_app.config['PRICE_PAISE'],
            status='pending'
        )
        db.session.add(payment)
        db.session.commit()
        return jsonify({'order_id': order['id'], 'amount': order['amount'], 'key': key_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Verify Payment ────────────────────────────────────────────────────────────

@api_bp.route('/verify-payment', methods=['POST'])
@login_required
def verify_payment():
    data       = request.get_json()
    key_secret = current_app.config.get('RAZORPAY_KEY_SECRET', '')

    if not key_secret:
        _activate_dev_subscription(None)
        return jsonify({'success': True})

    try:
        body     = data['razorpay_order_id'] + '|' + data['razorpay_payment_id']
        expected = hmac.new(key_secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        if expected != data['razorpay_signature']:
            return jsonify({'error': 'Payment verification failed.'}), 400

        payment = Payment.query.filter_by(razorpay_order=data['razorpay_order_id']).first()
        if payment:
            payment.razorpay_payment = data['razorpay_payment_id']
            payment.status           = 'paid'
            payment.set_expiry(current_app.config['SUBSCRIPTION_DAYS'])
            db.session.commit()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def _activate_dev_subscription(resume_id):
    from config import Config
    p = Payment(
        user_id=current_user.id, resume_id=resume_id,
        amount_paise=Config.PRICE_PAISE, status='paid'
    )
    p.set_expiry(Config.SUBSCRIPTION_DAYS)
    db.session.add(p)
    db.session.commit()


# ── Get Resume Data ───────────────────────────────────────────────────────────

@api_bp.route('/resume/<int:resume_id>', methods=['GET'])
@login_required
def get_resume(resume_id):
    resume = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first_or_404()
    return jsonify({
        'id':            resume.id,
        'original':      resume.original_text,
        'improved':      resume.improved_text or resume.original_text,
        'ats_score':     resume.ats_score,
        'improved_score':resume.improved_score,
        'mode':          resume.mode,
        'filename':      resume.filename,
    })

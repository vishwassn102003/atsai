from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import Resume, Payment

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    resumes  = Resume.query.filter_by(user_id=current_user.id) \
                           .order_by(Resume.updated_at.desc()).all()
    payments = Payment.query.filter_by(user_id=current_user.id) \
                            .order_by(Payment.created_at.desc()).all()
    sub    = current_user.active_sub()
    edits  = current_user.edits_remaining()
    return render_template('dashboard.html',
                           resumes=resumes, payments=payments,
                           sub=sub, edits_remaining=edits)


@main_bp.route('/checker')
@login_required
def checker():
    sub   = current_user.active_sub()
    edits = current_user.edits_remaining()
    return render_template('checker.html', sub=sub, edits_remaining=edits)


@main_bp.route('/editor/<int:resume_id>')
@login_required
def editor(resume_id):
    resume = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first_or_404()
    sub    = current_user.active_sub()
    edits  = current_user.edits_remaining()
    can_dl = current_user.can_download()
    return render_template('editor.html',
                           resume=resume, sub=sub,
                           edits_remaining=edits, can_download=can_dl)

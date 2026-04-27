from flask import Blueprint, redirect, url_for, session, current_app, request
from flask_login import login_user, logout_user, login_required, current_user
from models import User
from extensions import db
import requests as http

auth_bp = Blueprint('auth', __name__)

GOOGLE_AUTH_URL  = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_INFO_URL  = 'https://www.googleapis.com/oauth2/v3/userinfo'


def _redirect_uri():
    return url_for('auth.callback', _external=True)


@auth_bp.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    cid = current_app.config['GOOGLE_CLIENT_ID']
    params = (
        f"client_id={cid}"
        f"&redirect_uri={_redirect_uri()}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
        f"&access_type=offline"
        f"&prompt=select_account"
    )
    return redirect(f"{GOOGLE_AUTH_URL}?{params}")


@auth_bp.route('/auth/callback')
def callback():
    code  = request.args.get('code')
    error = request.args.get('error')
    if error or not code:
        return redirect(url_for('main.index'))

    token_resp = http.post(GOOGLE_TOKEN_URL, data={
        'code':          code,
        'client_id':     current_app.config['GOOGLE_CLIENT_ID'],
        'client_secret': current_app.config['GOOGLE_CLIENT_SECRET'],
        'redirect_uri':  _redirect_uri(),
        'grant_type':    'authorization_code',
    })
    tokens       = token_resp.json()
    access_token = tokens.get('access_token')
    if not access_token:
        return redirect(url_for('main.index'))

    info      = http.get(GOOGLE_INFO_URL, headers={'Authorization': f'Bearer {access_token}'}).json()
    google_id = info.get('sub')
    email     = info.get('email')
    name      = info.get('name')
    avatar    = info.get('picture')

    if not google_id or not email:
        return redirect(url_for('main.index'))

    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        user = User(google_id=google_id, email=email, name=name, avatar=avatar)
        db.session.add(user)
    else:
        user.name   = name
        user.avatar = avatar
    db.session.commit()

    login_user(user, remember=True)
    next_page = session.pop('next', None)
    return redirect(next_page or url_for('main.dashboard'))


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

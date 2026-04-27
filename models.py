from extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime, timedelta


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id         = db.Column(db.Integer, primary_key=True)
    google_id  = db.Column(db.String(128), unique=True, nullable=False)
    email      = db.Column(db.String(256), unique=True, nullable=False)
    name       = db.Column(db.String(256))
    avatar     = db.Column(db.String(512))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    resumes  = db.relationship('Resume',  backref='user', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='user', lazy=True, cascade='all, delete-orphan')

    def active_sub(self):
        now = datetime.utcnow()
        return Payment.query.filter_by(user_id=self.id, status='paid') \
                             .filter(Payment.expires_at > now) \
                             .order_by(Payment.created_at.desc()).first()

    def edits_used(self):
        sub = self.active_sub()
        if not sub:
            return 0
        return Resume.query.filter_by(user_id=self.id) \
                           .filter(Resume.updated_at >= sub.created_at).count()

    def edits_remaining(self):
        from config import Config
        sub = self.active_sub()
        if not sub:
            return 0
        return max(0, Config.SUBSCRIPTION_EDITS - self.edits_used())

    def can_edit(self):
        return self.edits_remaining() > 0

    def can_download(self):
        """User can download only if they have an active paid subscription."""
        return self.active_sub() is not None


class Resume(db.Model):
    __tablename__ = 'resumes'
    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename        = db.Column(db.String(256))
    original_text   = db.Column(db.Text)
    improved_text   = db.Column(db.Text)
    job_description = db.Column(db.Text)
    ats_score       = db.Column(db.Integer)
    improved_score  = db.Column(db.Integer)
    mode            = db.Column(db.String(32), default='with_jd')
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Payment(db.Model):
    __tablename__ = 'payments'
    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    resume_id        = db.Column(db.Integer, nullable=True)
    razorpay_order   = db.Column(db.String(128))
    razorpay_payment = db.Column(db.String(128))
    amount_paise     = db.Column(db.Integer)
    status           = db.Column(db.String(32), default='pending')
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at       = db.Column(db.DateTime)

    def set_expiry(self, days=30):
        self.expires_at = datetime.utcnow() + timedelta(days=days)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

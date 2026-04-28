import sys
import os

print("Starting app.py...", flush=True)

from flask import Flask
print("Flask imported", flush=True)

from extensions import db, login_manager
print("Extensions imported", flush=True)

from config import Config
print("Config imported", flush=True)

def create_app():
    print("Creating app...", flush=True)
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    print("Registering blueprints...", flush=True)
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    print("Creating DB tables...", flush=True)
    with app.app_context():
        db.create_all()

    print("App created successfully!", flush=True)
    return app

try:
    app = create_app()
    print("App ready to serve requests", flush=True)
except Exception as e:
    print(f"FATAL STARTUP ERROR: {type(e).__name__}: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
import redis
import os

# Importar modelos unificados
from modelos.models import db, Usuario

def criar_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    # Inicializar extensões
    login_manager = LoginManager()
    migrate = Migrate()
    
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Configurar login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    # Configurar user_loader para Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))
    
    # Configurar Redis
    app.redis = redis.from_url(app.config['REDIS_URL'])
    
    # Registrar blueprints
    from rotas.auth import bp as auth_bp
    from rotas.professor import bp as professor_bp
    from rotas.aluno import bp as aluno_bp
    from rotas.principal import bp as principal_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(professor_bp, url_prefix='/professor')
    app.register_blueprint(aluno_bp, url_prefix='/aluno')
    app.register_blueprint(principal_bp)
    
    # Criar diretórios necessários
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    return app

if __name__ == '__main__':
    app = criar_app()
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8000, debug=True)
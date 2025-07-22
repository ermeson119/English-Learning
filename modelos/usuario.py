from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Importação do db será feita dinamicamente
db = None

def init_db(database):
    global db
    db = database

def get_usuario_model():
    class Usuario(UserMixin, db.Model):
        __tablename__ = 'usuarios'
        
        id = db.Column(db.Integer, primary_key=True)
        nome = db.Column(db.String(100), nullable=False)
        email = db.Column(db.String(120), unique=True, nullable=False)
        senha_hash = db.Column(db.String(255), nullable=False)
        tipo_usuario = db.Column(db.String(20), nullable=False)  # 'professor' ou 'aluno'
        data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
        ativo = db.Column(db.Boolean, default=True)
        
        # Relacionamentos
        turmas_criadas = db.relationship('Turma', backref='professor', lazy=True, foreign_keys='Turma.professor_id')
        matriculas = db.relationship('Matricula', backref='aluno', lazy=True)
        progresso_atividades = db.relationship('ProgressoAtividade', backref='aluno', lazy=True)
        
        def definir_senha(self, senha):
            """Define a senha do usuário com hash"""
            self.senha_hash = generate_password_hash(senha)
        
        def verificar_senha(self, senha):
            """Verifica se a senha está correta"""
            return check_password_hash(self.senha_hash, senha)
        
        def eh_professor(self):
            """Verifica se o usuário é professor"""
            return self.tipo_usuario == 'professor'
        
        def eh_aluno(self):
            """Verifica se o usuário é aluno"""
            return self.tipo_usuario == 'aluno'
        
        def obter_turmas(self):
            """Obtém as turmas do usuário (criadas se professor, matriculado se aluno)"""
            if self.eh_professor():
                return self.turmas_criadas
            else:
                return [matricula.turma for matricula in self.matriculas if matricula.ativa]
        
        def __repr__(self):
            return f'<Usuario {self.nome}>'
    
    return Usuario

# Variável global para armazenar o modelo
Usuario = None

def get_usuario():
    global Usuario
    if Usuario is None:
        Usuario = get_usuario_model()
    return Usuario
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Inicialização do db
db = SQLAlchemy()

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

class Turma(db.Model):
    __tablename__ = 'turmas'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    codigo_acesso = db.Column(db.String(20), unique=True, nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    ativa = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    matriculas = db.relationship('Matricula', backref='turma', lazy=True, cascade='all, delete-orphan')
    modulos = db.relationship('Modulo', backref='turma', lazy=True, cascade='all, delete-orphan')
    
    def obter_alunos(self):
        """Obtém lista de alunos matriculados na turma"""
        return [matricula.aluno for matricula in self.matriculas if matricula.ativa]
    
    def obter_ranking(self):
        """Obtém ranking dos alunos da turma baseado na pontuação"""
        alunos_pontuacao = []
        for matricula in self.matriculas:
            if matricula.ativa:
                pontuacao_total = sum([
                    progresso.pontuacao for progresso in matricula.aluno.progresso_atividades
                ])
                alunos_pontuacao.append({
                    'aluno': matricula.aluno,
                    'pontuacao': pontuacao_total,
                    'data_matricula': matricula.data_matricula
                })
        
        # Ordenar por pontuação (decrescente) e depois por data de matrícula (crescente)
        return sorted(alunos_pontuacao, key=lambda x: (-x['pontuacao'], x['data_matricula']))
    
    def __repr__(self):
        return f'<Turma {self.nome}>'

class Matricula(db.Model):
    __tablename__ = 'matriculas'
    
    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    turma_id = db.Column(db.Integer, db.ForeignKey('turmas.id'), nullable=False)
    data_matricula = db.Column(db.DateTime, default=datetime.utcnow)
    ativa = db.Column(db.Boolean, default=True)
    
    __table_args__ = (db.UniqueConstraint('aluno_id', 'turma_id', name='_aluno_turma_uc'),)
    
    def __repr__(self):
        return f'<Matricula {self.aluno.nome} - {self.turma.nome}>'

class Modulo(db.Model):
    __tablename__ = 'modulos'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    ordem = db.Column(db.Integer, nullable=False)
    turma_id = db.Column(db.Integer, db.ForeignKey('turmas.id'), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    videos = db.relationship('Video', backref='modulo', lazy=True, cascade='all, delete-orphan')
    
    def obter_videos_ordenados(self):
        """Obtém vídeos do módulo ordenados por ordem"""
        return Video.query.filter_by(modulo_id=self.id, ativo=True).order_by(Video.ordem).all()
    
    def __repr__(self):
        return f'<Modulo {self.titulo}>'

class Video(db.Model):
    __tablename__ = 'videos'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    arquivo_video = db.Column(db.String(255), nullable=False)
    duracao = db.Column(db.Integer)  # em segundos
    ordem = db.Column(db.Integer, nullable=False)
    modulo_id = db.Column(db.Integer, db.ForeignKey('modulos.id'), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    atividades = db.relationship('Atividade', backref='video', lazy=True, cascade='all, delete-orphan')
    
    def obter_atividades(self):
        """Obtém atividades do vídeo"""
        return Atividade.query.filter_by(video_id=self.id, ativa=True).all()
    
    def __repr__(self):
        return f'<Video {self.titulo}>'

class Atividade(db.Model):
    __tablename__ = 'atividades'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    tipo_atividade = db.Column(db.String(50), nullable=False)  # 'multipla_escolha', 'completar', 'ordenar'
    pergunta = db.Column(db.Text, nullable=False)
    opcoes = db.Column(db.JSON)  # Para múltipla escolha
    resposta_correta = db.Column(db.Text, nullable=False)
    pontuacao_maxima = db.Column(db.Integer, default=10)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    ativa = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    progresso_atividades = db.relationship('ProgressoAtividade', backref='atividade', lazy=True)
    
    def __repr__(self):
        return f'<Atividade {self.titulo}>'

class ProgressoAtividade(db.Model):
    __tablename__ = 'progresso_atividades'
    
    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    atividade_id = db.Column(db.Integer, db.ForeignKey('atividades.id'), nullable=False)
    resposta_aluno = db.Column(db.Text)
    pontuacao = db.Column(db.Integer, default=0)
    concluida = db.Column(db.Boolean, default=False)
    tentativas = db.Column(db.Integer, default=0)
    data_primeira_tentativa = db.Column(db.DateTime, default=datetime.utcnow)
    data_ultima_tentativa = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('aluno_id', 'atividade_id', name='_aluno_atividade_uc'),)
    
    def calcular_pontuacao(self):
        """Calcula pontuação baseada na resposta e número de tentativas"""
        if self.resposta_aluno == self.atividade.resposta_correta:
            # Reduz pontuação baseada no número de tentativas
            reducao = (self.tentativas - 1) * 2
            pontuacao = max(self.atividade.pontuacao_maxima - reducao, 1)
            return pontuacao
        return 0
    
    def __repr__(self):
        return f'<ProgressoAtividade {self.aluno.nome} - {self.atividade.titulo}>' 
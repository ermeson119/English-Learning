from datetime import datetime

# Importação do db será feita dinamicamente
db = None

def init_db(database):
    global db
    db = database

def get_conteudo_model():
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
    
    return Modulo, Video, Atividade, ProgressoAtividade

# Variáveis globais para armazenar os modelos
Modulo = None
Video = None
Atividade = None
ProgressoAtividade = None

def get_modulo():
    global Modulo
    if Modulo is None:
        Modulo, _, _, _ = get_conteudo_model()
    return Modulo

def get_video():
    global Video
    if Video is None:
        _, Video, _, _ = get_conteudo_model()
    return Video

def get_atividade():
    global Atividade
    if Atividade is None:
        _, _, Atividade, _ = get_conteudo_model()
    return Atividade

def get_progresso_atividade():
    global ProgressoAtividade
    if ProgressoAtividade is None:
        _, _, _, ProgressoAtividade = get_conteudo_model()
    return ProgressoAtividade
from datetime import datetime

# Importação do db será feita dinamicamente
db = None

def init_db(database):
    global db
    db = database

def get_turma_model():
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
    
    return Turma, Matricula

# Variáveis globais para armazenar os modelos
Turma = None
Matricula = None

def get_turma():
    global Turma
    if Turma is None:
        Turma, _ = get_turma_model()
    return Turma

def get_matricula():
    global Matricula
    if Matricula is None:
        _, Matricula = get_turma_model()
    return Matricula
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from modelos.models import Usuario, Turma, Matricula, Modulo, Video, Atividade, ProgressoAtividade
from modelos.models import db
import secrets
import string
import os
import uuid
from werkzeug.utils import secure_filename

bp = Blueprint('professor', __name__)

def gerar_codigo_turma():
    """Gera código único para turma"""
    while True:
        codigo = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        if not Turma.query.filter_by(codigo_acesso=codigo).first():
            return codigo

@bp.before_request
def verificar_professor():
    """Verifica se o usuário é professor antes de acessar rotas"""
    if not current_user.is_authenticated or not current_user.eh_professor():
        flash('Acesso negado. Apenas professores podem acessar esta área.', 'danger')
        return redirect(url_for('principal.index'))

@bp.route('/dashboard')
@login_required
def dashboard():
    turmas = current_user.turmas_criadas
    estatisticas = {
        'total_turmas': len(turmas),
        'total_alunos': sum(len(turma.obter_alunos()) for turma in turmas),
        'turmas_ativas': len([t for t in turmas if t.ativa])
    }
    return render_template('professor/dashboard.html', turmas=turmas, estatisticas=estatisticas)

@bp.route('/turmas')
@login_required
def listar_turmas():
    turmas = current_user.turmas_criadas
    return render_template('professor/turmas.html', turmas=turmas)

@bp.route('/turmas/nova', methods=['GET', 'POST'])
@login_required
def criar_turma():
    if request.method == 'POST':
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        
        if not nome:
            flash('Nome da turma é obrigatório.', 'danger')
            return render_template('professor/criar_turma.html')
        
        nova_turma = Turma(
            nome=nome,
            descricao=descricao,
            codigo_acesso=gerar_codigo_turma(),
            professor_id=current_user.id
        )
        
        db.session.add(nova_turma)
        db.session.commit()
        
        flash(f'Turma "{nome}" criada com sucesso! Código de acesso: {nova_turma.codigo_acesso}', 'success')
        return redirect(url_for('professor.visualizar_turma', turma_id=nova_turma.id))
    
    return render_template('professor/criar_turma.html')

@bp.route('/turmas/<int:turma_id>')
@login_required
def visualizar_turma(turma_id):
    turma = Turma.query.filter_by(id=turma_id, professor_id=current_user.id).first_or_404()
    
    # Obter alunos com dados de matrícula
    matriculas = Matricula.query.filter_by(turma_id=turma.id, ativa=True).all()
    alunos_com_matricula = []
    for matricula in matriculas:
        aluno_data = {
            'aluno': matricula.aluno,
            'data_matricula': matricula.data_matricula
        }
        alunos_com_matricula.append(aluno_data)
    
    ranking = turma.obter_ranking()
    modulos = Modulo.query.filter_by(turma_id=turma.id, ativo=True).order_by(Modulo.ordem).all()
    
    return render_template('professor/turma_detalhes.html', 
                         turma=turma, alunos=alunos_com_matricula, ranking=ranking, modulos=modulos)

@bp.route('/turmas/<int:turma_id>/modulos/novo', methods=['GET', 'POST'])
@login_required
def criar_modulo(turma_id):
    turma = Turma.query.filter_by(id=turma_id, professor_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descricao = request.form.get('descricao')
        
        if not titulo:
            flash('Título do módulo é obrigatório.', 'danger')
            return render_template('professor/criar_modulo.html', turma=turma)
        
        # Determinar próxima ordem
        ultimo_modulo = Modulo.query.filter_by(turma_id=turma.id).order_by(Modulo.ordem.desc()).first()
        proxima_ordem = (ultimo_modulo.ordem + 1) if ultimo_modulo else 1
        
        novo_modulo = Modulo(
            titulo=titulo,
            descricao=descricao,
            ordem=proxima_ordem,
            turma_id=turma.id
        )
        
        db.session.add(novo_modulo)
        db.session.commit()
        
        flash(f'Módulo "{titulo}" criado com sucesso!', 'success')
        return redirect(url_for('professor.visualizar_turma', turma_id=turma.id))
    
    return render_template('professor/criar_modulo.html', turma=turma)

@bp.route('/modulos/<int:modulo_id>/videos/novo', methods=['GET', 'POST'])
@login_required
def criar_video(modulo_id):
    modulo = Modulo.query.join(Turma).filter(
        Modulo.id == modulo_id,
        Turma.professor_id == current_user.id
    ).first_or_404()
    
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descricao = request.form.get('descricao')
        duracao = request.form.get('duracao')
        
        # Verificar se arquivo foi enviado
        if 'arquivo_video' not in request.files:
            flash('Nenhum arquivo foi selecionado.', 'danger')
            return render_template('professor/criar_video.html', modulo=modulo)
        
        arquivo = request.files['arquivo_video']
        
        if arquivo.filename == '':
            flash('Nenhum arquivo foi selecionado.', 'danger')
            return render_template('professor/criar_video.html', modulo=modulo)
        
        if not titulo:
            flash('Título do vídeo é obrigatório.', 'danger')
            return render_template('professor/criar_video.html', modulo=modulo)
        
        # Verificar extensão do arquivo
        extensoes_permitidas = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'm4v'}
        if '.' not in arquivo.filename or \
           arquivo.filename.rsplit('.', 1)[1].lower() not in extensoes_permitidas:
            flash('Formato de arquivo não suportado. Use: MP4, AVI, MOV, MKV, WEBM, M4V', 'danger')
            return render_template('professor/criar_video.html', modulo=modulo)
        
        # Verificar tamanho do arquivo (máximo 1GB)
        arquivo.seek(0, os.SEEK_END)
        tamanho = arquivo.tell()
        arquivo.seek(0)
        
        if tamanho > 1024 * 1024 * 1024:  # 1GB
            flash('Arquivo muito grande. Tamanho máximo: 1GB', 'danger')
            return render_template('professor/criar_video.html', modulo=modulo)
        
        # Salvar arquivo
        try:
            # Criar diretório se não existir
            upload_dir = os.path.join('static', 'uploads', 'videos')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Gerar nome único para o arquivo
            nome_arquivo = secure_filename(arquivo.filename)
            nome_base, extensao = os.path.splitext(nome_arquivo)
            nome_unico = f"{uuid.uuid4().hex}_{nome_base}{extensao}"
            caminho_arquivo = os.path.join(upload_dir, nome_unico)
            
            # Salvar arquivo
            arquivo.save(caminho_arquivo)
            
            # Calcular duração se fornecida
            duracao_segundos = None
            if duracao:
                try:
                    duracao_segundos = int(duracao) * 60  # Converter minutos para segundos
                except ValueError:
                    pass
            
            # Determinar próxima ordem
            ultimo_video = Video.query.filter_by(modulo_id=modulo.id).order_by(Video.ordem.desc()).first()
            proxima_ordem = (ultimo_video.ordem + 1) if ultimo_video else 1
            
            novo_video = Video(
                titulo=titulo,
                descricao=descricao,
                arquivo_video=f'uploads/videos/{nome_unico}',  # Caminho relativo
                duracao=duracao_segundos,
                ordem=proxima_ordem,
                modulo_id=modulo.id
            )
            
            db.session.add(novo_video)
            db.session.commit()
            
            flash(f'Vídeo "{titulo}" adicionado com sucesso!', 'success')
            return redirect(url_for('professor.visualizar_turma', turma_id=modulo.turma_id))
            
        except Exception as e:
            flash(f'Erro ao salvar arquivo: {str(e)}', 'danger')
            return render_template('professor/criar_video.html', modulo=modulo)
    
    return render_template('professor/criar_video.html', modulo=modulo)

@bp.route('/videos/<path:filename>')
def servir_video(filename):
    """Serve arquivos de vídeo com tipo MIME correto"""
    from flask import send_from_directory, Response, current_app
    import mimetypes
    import os
    
    # Caminho completo do arquivo
    video_path = os.path.join(current_app.root_path, 'static', 'uploads', 'videos', filename)
    
    # Debug: verificar se arquivo existe
    if not os.path.exists(video_path):
        current_app.logger.error(f"Arquivo não encontrado: {video_path}")
        return f"Arquivo não encontrado: {filename}", 404
    
    current_app.logger.info(f"Servindo vídeo: {filename} - Tamanho: {os.path.getsize(video_path)} bytes")
    
    # Detectar tipo MIME baseado na extensão
    mime_type, _ = mimetypes.guess_type(filename)
    
    # Mapear extensões para tipos MIME específicos
    mime_map = {
        '.mp4': 'video/mp4',
        '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime',
        '.mkv': 'video/x-matroska',
        '.webm': 'video/webm',
        '.m4v': 'video/x-m4v'
    }
    
    # Obter extensão do arquivo
    _, ext = os.path.splitext(filename.lower())
    if ext in mime_map:
        mime_type = mime_map[ext]
    elif not mime_type:
        mime_type = 'video/mp4'  # Fallback
    
    # Servir arquivo com tipo MIME correto
    return send_from_directory(
        'static/uploads/videos', 
        filename,
        mimetype=mime_type
    )

@bp.route('/videos/<int:video_id>/atividades/nova', methods=['GET', 'POST'])
@login_required
def criar_atividade(video_id):
    video = Video.query.join(Modulo).join(Turma).filter(
        Video.id == video_id,
        Turma.professor_id == current_user.id
    ).first_or_404()
    
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        tipo_atividade = request.form.get('tipo_atividade')
        pergunta = request.form.get('pergunta')
        resposta_correta = request.form.get('resposta_correta')
        pontuacao_maxima = int(request.form.get('pontuacao_maxima', 10))
        
        opcoes = None
        if tipo_atividade == 'multipla_escolha':
            opcoes = [
                request.form.get('opcao_1'),
                request.form.get('opcao_2'),
                request.form.get('opcao_3'),
                request.form.get('opcao_4')
            ]
            opcoes = [op for op in opcoes if op]  # Remove opções vazias
        
        if not all([titulo, tipo_atividade, pergunta, resposta_correta]):
            flash('Todos os campos obrigatórios devem ser preenchidos.', 'danger')
            return render_template('professor/criar_atividade.html', video=video)
        
        nova_atividade = Atividade(
            titulo=titulo,
            tipo_atividade=tipo_atividade,
            pergunta=pergunta,
            opcoes=opcoes,
            resposta_correta=resposta_correta,
            pontuacao_maxima=pontuacao_maxima,
            video_id=video.id
        )
        
        db.session.add(nova_atividade)
        db.session.commit()
        
        flash(f'Atividade "{titulo}" criada com sucesso!', 'success')
        return redirect(url_for('professor.visualizar_turma', turma_id=video.modulo.turma_id))
    
    return render_template('professor/criar_atividade.html', video=video)

@bp.route('/relatorios/turma/<int:turma_id>')
@login_required
def relatorio_turma(turma_id):
    turma = Turma.query.filter_by(id=turma_id, professor_id=current_user.id).first_or_404()
    
    # Dados para relatório
    alunos_progresso = []
    for matricula in turma.matriculas:
        if matricula.ativa:
            aluno = matricula.aluno
            total_atividades = 0
            atividades_concluidas = 0
            pontuacao_total = 0
            
            for modulo in turma.modulos:
                for video in modulo.videos:
                    for atividade in video.atividades:
                        total_atividades += 1
                        progresso = ProgressoAtividade.query.filter_by(
                            aluno_id=aluno.id,
                            atividade_id=atividade.id
                        ).first()
                        
                        if progresso and progresso.concluida:
                            atividades_concluidas += 1
                            pontuacao_total += progresso.pontuacao
            
            percentual_conclusao = (atividades_concluidas / total_atividades * 100) if total_atividades > 0 else 0
            
            alunos_progresso.append({
                'aluno': aluno,
                'total_atividades': total_atividades,
                'atividades_concluidas': atividades_concluidas,
                'percentual_conclusao': round(percentual_conclusao, 1),
                'pontuacao_total': pontuacao_total
            })
    
    return render_template('professor/relatorio_turma.html', 
                         turma=turma, alunos_progresso=alunos_progresso)
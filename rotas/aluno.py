from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from modelos.models import Usuario, Turma, Matricula, Modulo, Video, Atividade, ProgressoAtividade, db
from datetime import datetime

bp = Blueprint('aluno', __name__)

@bp.before_request
def verificar_aluno():
    """Verifica se o usuário é aluno antes de acessar rotas"""
    if not current_user.is_authenticated or not current_user.eh_aluno():
        flash('Acesso negado. Apenas alunos podem acessar esta área.', 'danger')
        return redirect(url_for('principal.index'))

@bp.route('/dashboard')
@login_required
def dashboard():
    turmas = current_user.obter_turmas()
    
    # Calcular estatísticas
    total_atividades = 0
    atividades_concluidas = 0
    pontuacao_total = 0
    
    for turma in turmas:
        for modulo in turma.modulos:
            for video in modulo.videos:
                for atividade in video.atividades:
                    total_atividades += 1
                    progresso = ProgressoAtividade.query.filter_by(
                        aluno_id=current_user.id,
                        atividade_id=atividade.id
                    ).first()
                    
                    if progresso and progresso.concluida:
                        atividades_concluidas += 1
                        pontuacao_total += progresso.pontuacao
    
    percentual_conclusao = (atividades_concluidas / total_atividades * 100) if total_atividades > 0 else 0
    
    estatisticas = {
        'total_turmas': len(turmas),
        'total_atividades': total_atividades,
        'atividades_concluidas': atividades_concluidas,
        'percentual_conclusao': round(percentual_conclusao, 1),
        'pontuacao_total': pontuacao_total
    }
    
    return render_template('aluno/dashboard.html', turmas=turmas, estatisticas=estatisticas)

@bp.route('/turmas')
@login_required
def listar_turmas():
    turmas = current_user.obter_turmas()
    return render_template('aluno/turmas.html', turmas=turmas)

@bp.route('/turmas/entrar', methods=['GET', 'POST'])
@login_required
def entrar_turma():
    if request.method == 'POST':
        codigo_acesso = request.form.get('codigo_acesso', '').strip().upper()
        
        if not codigo_acesso:
            flash('Código de acesso é obrigatório.', 'danger')
            return render_template('aluno/entrar_turma.html')
        
        turma = Turma.query.filter_by(codigo_acesso=codigo_acesso, ativa=True).first()
        
        if not turma:
            flash('Código de acesso inválido ou turma inativa.', 'danger')
            return render_template('aluno/entrar_turma.html')
        
        # Verificar se já está matriculado
        matricula_existente = Matricula.query.filter_by(
            aluno_id=current_user.id,
            turma_id=turma.id
        ).first()
        
        if matricula_existente:
            if matricula_existente.ativa:
                flash('Você já está matriculado nesta turma.', 'info')
            else:
                # Reativar matrícula
                matricula_existente.ativa = True
                db.session.commit()
                flash(f'Matrícula reativada na turma "{turma.nome}".', 'success')
        else:
            # Criar nova matrícula
            nova_matricula = Matricula(
                aluno_id=current_user.id,
                turma_id=turma.id
            )
            db.session.add(nova_matricula)
            db.session.commit()
            flash(f'Matrícula realizada com sucesso na turma "{turma.nome}".', 'success')
        
        return redirect(url_for('aluno.visualizar_turma', turma_id=turma.id))
    
    return render_template('aluno/entrar_turma.html')

@bp.route('/turmas/<int:turma_id>')
@login_required
def visualizar_turma(turma_id):
    # Verificar se está matriculado na turma
    matricula = Matricula.query.filter_by(
        aluno_id=current_user.id,
        turma_id=turma_id,
        ativa=True
    ).first_or_404()
    
    turma = matricula.turma
    modulos = Modulo.query.filter_by(turma_id=turma.id, ativo=True).order_by(Modulo.ordem).all()
    ranking = turma.obter_ranking()
    
    # Encontrar posição do aluno no ranking
    posicao_aluno = None
    for i, item in enumerate(ranking):
        if item['aluno'].id == current_user.id:
            posicao_aluno = i + 1
            break
    
    return render_template('aluno/turma_detalhes.html', 
                         turma=turma, modulos=modulos, ranking=ranking, posicao_aluno=posicao_aluno)

@bp.route('/videos/<int:video_id>')
@login_required
def assistir_video(video_id):
    video = Video.query.join(Modulo).join(Turma).join(Matricula).filter(
        Video.id == video_id,
        Matricula.aluno_id == current_user.id,
        Matricula.ativa == True
    ).first_or_404()
    
    atividades = video.obter_atividades()
    
    # Obter progresso das atividades
    progresso_atividades = {}
    for atividade in atividades:
        progresso = ProgressoAtividade.query.filter_by(
            aluno_id=current_user.id,
            atividade_id=atividade.id
        ).first()
        progresso_atividades[atividade.id] = progresso
    
    return render_template('aluno/assistir_video.html', 
                         video=video, atividades=atividades, progresso_atividades=progresso_atividades)

@bp.route('/atividades/<int:atividade_id>/responder', methods=['POST'])
@login_required
def responder_atividade(atividade_id):
    atividade = Atividade.query.join(Video).join(Modulo).join(Turma).join(Matricula).filter(
        Atividade.id == atividade_id,
        Matricula.aluno_id == current_user.id,
        Matricula.ativa == True
    ).first_or_404()
    
    resposta_aluno = request.form.get('resposta', '').strip()
    
    if not resposta_aluno:
        return jsonify({'sucesso': False, 'mensagem': 'Resposta é obrigatória.'})
    
    # Obter ou criar progresso
    progresso = ProgressoAtividade.query.filter_by(
        aluno_id=current_user.id,
        atividade_id=atividade.id
    ).first()
    
    if not progresso:
        progresso = ProgressoAtividade(
            aluno_id=current_user.id,
            atividade_id=atividade.id
        )
        db.session.add(progresso)
    
    # Atualizar progresso
    progresso.resposta_aluno = resposta_aluno
    progresso.tentativas += 1
    progresso.data_ultima_tentativa = datetime.utcnow()
    
    # Verificar resposta
    resposta_correta = resposta_aluno.lower() == atividade.resposta_correta.lower()
    
    if resposta_correta:
        progresso.concluida = True
        progresso.pontuacao = progresso.calcular_pontuacao()
        mensagem = f'Parabéns! Resposta correta. Você ganhou {progresso.pontuacao} pontos!'
        tipo_mensagem = 'success'
    else:
        progresso.concluida = False
        progresso.pontuacao = 0
        mensagem = f'Resposta incorreta. Tente novamente! (Tentativa {progresso.tentativas})'
        tipo_mensagem = 'danger'
    
    db.session.commit()
    
    return jsonify({
        'sucesso': resposta_correta,
        'mensagem': mensagem,
        'tipo_mensagem': tipo_mensagem,
        'pontuacao': progresso.pontuacao,
        'tentativas': progresso.tentativas
    })

@bp.route('/progresso')
@login_required
def meu_progresso():
    turmas = current_user.obter_turmas()
    
    progresso_detalhado = []
    for turma in turmas:
        progresso_turma = {
            'turma': turma,
            'modulos': []
        }
        
        for modulo in turma.modulos:
            progresso_modulo = {
                'modulo': modulo,
                'videos': []
            }
            
            for video in modulo.videos:
                total_atividades = len(video.atividades)
                atividades_concluidas = 0
                pontuacao_video = 0
                
                for atividade in video.atividades:
                    progresso = ProgressoAtividade.query.filter_by(
                        aluno_id=current_user.id,
                        atividade_id=atividade.id
                    ).first()
                    
                    if progresso and progresso.concluida:
                        atividades_concluidas += 1
                        pontuacao_video += progresso.pontuacao
                
                percentual = (atividades_concluidas / total_atividades * 100) if total_atividades > 0 else 0
                
                progresso_modulo['videos'].append({
                    'video': video,
                    'total_atividades': total_atividades,
                    'atividades_concluidas': atividades_concluidas,
                    'percentual_conclusao': round(percentual, 1),
                    'pontuacao': pontuacao_video
                })
            
            progresso_turma['modulos'].append(progresso_modulo)
        
        progresso_detalhado.append(progresso_turma)
    
    return render_template('aluno/progresso.html', progresso_detalhado=progresso_detalhado)
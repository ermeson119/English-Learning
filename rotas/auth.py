from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from modelos.models import db, Usuario
import secrets
import string

bp = Blueprint('auth', __name__)



@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('principal.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        lembrar = bool(request.form.get('lembrar'))
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and usuario.verificar_senha(senha) and usuario.ativo:
            login_user(usuario, remember=lembrar)
            
            # Redirecionar para página solicitada ou dashboard
            proxima_pagina = request.args.get('next')
            if not proxima_pagina or url_parse(proxima_pagina).netloc != '':
                proxima_pagina = url_for('principal.dashboard')
            
            flash(f'Bem-vindo(a), {usuario.nome}!', 'success')
            return redirect(proxima_pagina)
        else:
            flash('Email ou senha incorretos.', 'danger')
    
    return render_template('auth/login.html')

@bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('principal.dashboard'))
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        confirmar_senha = request.form.get('confirmar_senha')
        tipo_usuario = request.form.get('tipo_usuario')
        
        # Validações
        if not all([nome, email, senha, confirmar_senha, tipo_usuario]):
            flash('Todos os campos são obrigatórios.', 'danger')
            return render_template('auth/registro.html')
        
        if senha != confirmar_senha:
            flash('As senhas não coincidem.', 'danger')
            return render_template('auth/registro.html')
        
        if len(senha) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'danger')
            return render_template('auth/registro.html')
        
        if tipo_usuario not in ['professor', 'aluno']:
            flash('Tipo de usuário inválido.', 'danger')
            return render_template('auth/registro.html')
        
        # Verificar se email já existe
        if Usuario.query.filter_by(email=email).first():
            flash('Este email já está cadastrado.', 'danger')
            return render_template('auth/registro.html')
        
        # Criar novo usuário
        novo_usuario = Usuario(
            nome=nome,
            email=email,
            tipo_usuario=tipo_usuario
        )
        novo_usuario.definir_senha(senha)
        
        db.session.add(novo_usuario)
        db.session.commit()
        
        flash('Cadastro realizado com sucesso! Faça login para continuar.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/registro.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado com sucesso.', 'info')
    return redirect(url_for('principal.index'))
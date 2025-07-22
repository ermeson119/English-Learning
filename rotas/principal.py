from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

bp = Blueprint('principal', __name__)

@bp.route('/')
def index():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('principal.dashboard'))
    except:
        pass
    return render_template('principal/index.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.eh_professor():
        return redirect(url_for('professor.dashboard'))
    else:
        return redirect(url_for('aluno.dashboard'))

@bp.route('/sobre')
def sobre():
    return render_template('principal/sobre.html')
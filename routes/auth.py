from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.models import db, Usuario, LogAcesso
from utils.auth_helpers import (
    hash_senha, verificar_senha, criar_sessao, get_usuario_atual,
    registrar_log_acesso, limpar_sessoes_expiradas
)
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')

        if not email or not senha:
            flash('Por favor, preencha todos os campos.', 'error')
            return render_template('auth/login.html')

        try:
            usuario = Usuario.query.filter_by(email=email, ativo=True).first()

            if not usuario:
                registrar_log_acesso(
                    None, 'login',
                    request.remote_addr,
                    request.headers.get('User-Agent'),
                    {'email': email, 'motivo': 'usuario_nao_encontrado'},
                    False
                )
                flash('Email ou senha incorretos.', 'error')
                return render_template('auth/login.html')

            if not verificar_senha(senha, usuario.senha_hash):
                registrar_log_acesso(
                    usuario.id, 'login',
                    request.remote_addr,
                    request.headers.get('User-Agent'),
                    {'motivo': 'senha_incorreta'},
                    False
                )
                flash('Email ou senha incorretos.', 'error')
                return render_template('auth/login.html')

            limpar_sessoes_expiradas()

            token_sessao = criar_sessao(
                usuario.id,
                request.remote_addr,
                request.headers.get('User-Agent')
            )

            if not token_sessao:
                flash('Erro ao criar sessão. Tente novamente.', 'error')
                return render_template('auth/login.html')

            session['token_sessao'] = token_sessao
            session['usuario_id'] = usuario.id
            session['perfil'] = usuario.perfil
            session['nome'] = usuario.nome

            registrar_log_acesso(
                usuario.id, 'login',
                request.remote_addr,
                request.headers.get('User-Agent'),
                None,
                True
            )

            flash(f'Bem-vindo(a), {usuario.nome}!', 'success')

            if usuario.perfil == 'admin':
                return redirect(url_for('index'))
            elif usuario.perfil == 'medico':
                return redirect(url_for('medico.dashboard'))
            elif usuario.perfil == 'recepcionista':
                return redirect(url_for('agendamento.lista_agendamentos'))
            else:
                return redirect(url_for('index'))

        except Exception as e:
            print(f"Erro no login: {e}")
            flash('Erro ao processar login. Tente novamente.', 'error')
            return render_template('auth/login.html')

    usuario_logado = get_usuario_atual()
    if usuario_logado:
        if usuario_logado.perfil == 'medico':
            return redirect(url_for('medico.dashboard'))
        elif usuario_logado.perfil == 'recepcionista':
            return redirect(url_for('agendamento.lista_agendamentos'))
        return redirect(url_for('index'))

    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    usuario = get_usuario_atual()
    token_sessao = session.get('token_sessao')

    if usuario and token_sessao:
        try:
            from models.models import SessaoUsuario
            SessaoUsuario.query.filter_by(token_sessao=token_sessao).delete()
            db.session.commit()

            registrar_log_acesso(
                usuario.id, 'logout',
                request.remote_addr,
                request.headers.get('User-Agent')
            )
        except Exception as e:
            print(f"Erro ao fazer logout: {e}")
            db.session.rollback()

    session.clear()
    flash('Você saiu do sistema.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/perfil')
def perfil():
    usuario = get_usuario_atual()
    if not usuario:
        flash('Você precisa fazer login.', 'error')
        return redirect(url_for('auth.login'))

    try:
        logs_recentes = LogAcesso.query.filter_by(usuario_id=usuario.id)\
            .order_by(LogAcesso.data_criacao.desc())\
            .limit(10)\
            .all()

        return render_template('auth/perfil.html',
                             usuario=usuario,
                             logs=logs_recentes)
    except Exception as e:
        print(f"Erro ao carregar perfil: {e}")
        return render_template('auth/perfil.html', usuario=usuario, logs=[])

@auth_bp.route('/alterar-senha', methods=['GET', 'POST'])
def alterar_senha():
    usuario = get_usuario_atual()
    if not usuario:
        flash('Você precisa fazer login.', 'error')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        senha_atual = request.form.get('senha_atual', '')
        senha_nova = request.form.get('senha_nova', '')
        senha_confirmacao = request.form.get('senha_confirmacao', '')

        if not senha_atual or not senha_nova or not senha_confirmacao:
            flash('Preencha todos os campos.', 'error')
            return render_template('auth/alterar_senha.html')

        if senha_nova != senha_confirmacao:
            flash('A nova senha e a confirmação não coincidem.', 'error')
            return render_template('auth/alterar_senha.html')

        if len(senha_nova) < 6:
            flash('A nova senha deve ter pelo menos 6 caracteres.', 'error')
            return render_template('auth/alterar_senha.html')

        try:
            usuario_db = Usuario.query.filter_by(id=usuario.id).first()

            if not verificar_senha(senha_atual, usuario_db.senha_hash):
                flash('Senha atual incorreta.', 'error')
                return render_template('auth/alterar_senha.html')

            nova_senha_hash = hash_senha(senha_nova)
            usuario_db.senha_hash = nova_senha_hash
            db.session.commit()

            registrar_log_acesso(
                usuario.id, 'senha_alterada',
                request.remote_addr,
                request.headers.get('User-Agent')
            )

            flash('Senha alterada com sucesso!', 'success')
            return redirect(url_for('auth.perfil'))

        except Exception as e:
            print(f"Erro ao alterar senha: {e}")
            db.session.rollback()
            flash('Erro ao alterar senha. Tente novamente.', 'error')
            return render_template('auth/alterar_senha.html')

    return render_template('auth/alterar_senha.html')

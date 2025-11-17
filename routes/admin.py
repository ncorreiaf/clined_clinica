from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.models import db, Usuario, LogAcesso, Profissional
from utils.auth_helpers import admin_required, get_usuario_atual, hash_senha, gerar_token_tv
from datetime import datetime
import json

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/usuarios')
@admin_required
def listar_usuarios():
    usuario = get_usuario_atual()

    try:
        usuarios = Usuario.query.order_by(Usuario.data_criacao.desc()).all()

        return render_template('admin/usuarios.html',
                             usuario=usuario,
                             usuarios=usuarios)
    except Exception as e:
        flash(f'Erro ao carregar usuários: {str(e)}', 'error')
        return render_template('admin/usuarios.html', usuario=usuario, usuarios=[])

@admin_bp.route('/usuarios/novo', methods=['GET', 'POST'])
@admin_required
def novo_usuario():
    usuario = get_usuario_atual()

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        perfil = request.form.get('perfil', '')
        profissional_id = request.form.get('profissional_id', '')

        if not nome or not email or not senha or not perfil:
            flash('Preencha todos os campos obrigatórios.', 'error')
            return render_template('admin/novo_usuario.html', usuario=usuario)

        if perfil not in ['admin', 'medico', 'tv']:
            flash('Perfil inválido.', 'error')
            return render_template('admin/novo_usuario.html', usuario=usuario)

        if len(senha) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'error')
            return render_template('admin/novo_usuario.html', usuario=usuario)

        try:
            usuario_existente = Usuario.query.filter_by(email=email).first()

            if usuario_existente:
                flash('Já existe um usuário com este email.', 'error')
                return render_template('admin/novo_usuario.html', usuario=usuario)

            senha_hash = hash_senha(senha)

            novo_usuario = Usuario(
                nome=nome,
                email=email,
                senha_hash=senha_hash,
                perfil=perfil,
                ativo=True
            )

            if perfil == 'medico' and profissional_id:
                novo_usuario.profissional_id = int(profissional_id)

            if perfil == 'tv':
                novo_usuario.token_tv = gerar_token_tv()

            db.session.add(novo_usuario)
            db.session.commit()

            if perfil == 'tv':
                flash(f'Usuário criado com sucesso! Token de acesso TV: {novo_usuario.token_tv}', 'success')
            else:
                flash('Usuário criado com sucesso!', 'success')

            return redirect(url_for('admin.listar_usuarios'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar usuário: {str(e)}', 'error')
            return render_template('admin/novo_usuario.html', usuario=usuario)

    return render_template('admin/novo_usuario.html', usuario=usuario)

@admin_bp.route('/usuarios/<int:usuario_id>/editar', methods=['GET', 'POST'])
@admin_required
def editar_usuario(usuario_id):
    usuario_logado = get_usuario_atual()

    try:
        usuario_editando = Usuario.query.get(usuario_id)

        if not usuario_editando:
            flash('Usuário não encontrado.', 'error')
            return redirect(url_for('admin.listar_usuarios'))

        if request.method == 'POST':
            nome = request.form.get('nome', '').strip()
            email = request.form.get('email', '').strip()
            ativo = request.form.get('ativo') == 'on'
            nova_senha = request.form.get('nova_senha', '')

            if not nome or not email:
                flash('Nome e email são obrigatórios.', 'error')
                return render_template('admin/editar_usuario.html',
                                     usuario=usuario_logado,
                                     usuario_editando=usuario_editando)

            usuario_editando.nome = nome
            usuario_editando.email = email
            usuario_editando.ativo = ativo

            if nova_senha:
                if len(nova_senha) < 6:
                    flash('A nova senha deve ter pelo menos 6 caracteres.', 'error')
                    return render_template('admin/editar_usuario.html',
                                         usuario=usuario_logado,
                                         usuario_editando=usuario_editando)
                usuario_editando.senha_hash = hash_senha(nova_senha)

            db.session.commit()

            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('admin.listar_usuarios'))

        return render_template('admin/editar_usuario.html',
                             usuario=usuario_logado,
                             usuario_editando=usuario_editando)

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao editar usuário: {str(e)}', 'error')
        return redirect(url_for('admin.listar_usuarios'))

@admin_bp.route('/usuarios/<int:usuario_id>/desativar', methods=['POST'])
@admin_required
def desativar_usuario(usuario_id):
    try:
        usuario = Usuario.query.get(usuario_id)
        if usuario:
            usuario.ativo = False
            db.session.commit()
            flash('Usuário desativado com sucesso!', 'success')
        else:
            flash('Usuário não encontrado.', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao desativar usuário: {str(e)}', 'error')

    return redirect(url_for('admin.listar_usuarios'))

@admin_bp.route('/logs')
@admin_required
def logs_acesso():
    usuario = get_usuario_atual()

    try:
        logs = LogAcesso.query\
            .order_by(LogAcesso.data_criacao.desc())\
            .limit(100)\
            .all()

        logs_com_usuario = []
        for log in logs:
            log_dict = {
                'id': log.id,
                'acao': log.acao,
                'ip_address': log.ip_address,
                'user_agent': log.user_agent,
                'detalhes': log.detalhes,
                'sucesso': log.sucesso,
                'data_criacao': log.data_criacao,
                'usuario': None
            }

            if log.usuario_id:
                usuario_log = Usuario.query.get(log.usuario_id)
                if usuario_log:
                    log_dict['usuario'] = {
                        'nome': usuario_log.nome,
                        'email': usuario_log.email
                    }

            logs_com_usuario.append(log_dict)

        return render_template('admin/logs.html',
                             usuario=usuario,
                             logs=logs_com_usuario)
    except Exception as e:
        flash(f'Erro ao carregar logs: {str(e)}', 'error')
        return render_template('admin/logs.html', usuario=usuario, logs=[])

@admin_bp.route('/token-tv')
@admin_required
def token_tv():
    usuario = get_usuario_atual()

    try:
        usuario_tv = Usuario.query.filter_by(perfil='tv', ativo=True).first()

        if not usuario_tv or not usuario_tv.token_tv:
            flash('Nenhum usuário de TV encontrado ou token não disponível.', 'error')
            token_tv_value = None
            url_completa = None
        else:
            token_tv_value = usuario_tv.token_tv
            url_completa = request.host_url.rstrip('/') + url_for('chamados.painel_tv', token=token_tv_value)

        return render_template('admin/token_tv.html',
                             usuario=usuario,
                             token_tv=token_tv_value,
                             url_completa=url_completa)
    except Exception as e:
        flash(f'Erro ao carregar token TV: {str(e)}', 'error')
        return render_template('admin/token_tv.html', usuario=usuario, token_tv=None, url_completa=None)

@admin_bp.route('/token-tv/gerar-novo', methods=['POST'])
@admin_required
def gerar_novo_token_tv():
    try:
        usuario_tv = Usuario.query.filter_by(perfil='tv', ativo=True).first()

        if not usuario_tv:
            flash('Nenhum usuário de TV encontrado.', 'error')
        else:
            novo_token = gerar_token_tv()
            usuario_tv.token_tv = novo_token
            db.session.commit()
            flash('Novo token de TV gerado com sucesso!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao gerar novo token: {str(e)}', 'error')

    return redirect(url_for('admin.token_tv'))

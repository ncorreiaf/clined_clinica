import bcrypt
import secrets
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import session, redirect, url_for, flash, request
from models.models import db, Usuario, SessaoUsuario, LogAcesso

def hash_senha(senha: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')

def verificar_senha(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8'))

def gerar_token_sessao() -> str:
    return secrets.token_urlsafe(32)

def gerar_token_tv() -> str:
    return secrets.token_urlsafe(48)

def criar_sessao(usuario_id: int, ip_address: str = None, user_agent: str = None):
    token_sessao = gerar_token_sessao()
    expira_em = datetime.now() + timedelta(hours=24)

    try:
        nova_sessao = SessaoUsuario(
            usuario_id=usuario_id,
            token_sessao=token_sessao,
            ip_address=ip_address,
            user_agent=user_agent,
            expira_em=expira_em
        )
        db.session.add(nova_sessao)
        db.session.commit()
        return token_sessao
    except Exception as e:
        print(f"Erro ao criar sessão: {e}")
        db.session.rollback()
        return None

def validar_sessao(token_sessao: str):
    try:
        sessao = SessaoUsuario.query.filter_by(token_sessao=token_sessao).first()

        if not sessao:
            return None

        if sessao.expira_em < datetime.now():
            db.session.delete(sessao)
            db.session.commit()
            return None

        usuario = Usuario.query.filter_by(id=sessao.usuario_id, ativo=True).first()

        if usuario:
            usuario.ultimo_acesso = datetime.now()
            db.session.commit()
            return usuario

        return None
    except Exception as e:
        print(f"Erro ao validar sessão: {e}")
        db.session.rollback()
        return None

def registrar_log_acesso(usuario_id: int = None, acao: str = '', ip_address: str = None,
                        user_agent: str = None, detalhes: dict = None, sucesso: bool = True):
    try:
        log = LogAcesso(
            usuario_id=usuario_id,
            acao=acao,
            ip_address=ip_address,
            user_agent=user_agent,
            detalhes=json.dumps(detalhes) if detalhes else None,
            sucesso=sucesso
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Erro ao registrar log: {e}")
        db.session.rollback()

def limpar_sessoes_expiradas():
    try:
        SessaoUsuario.query.filter(SessaoUsuario.expira_em < datetime.now()).delete()
        db.session.commit()
    except Exception as e:
        print(f"Erro ao limpar sessões: {e}")
        db.session.rollback()

def get_usuario_atual():
    token_sessao = session.get('token_sessao')
    if not token_sessao:
        return None
    return validar_sessao(token_sessao)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        usuario = get_usuario_atual()
        if not usuario:
            flash('Você precisa fazer login para acessar esta página.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        usuario = get_usuario_atual()
        if not usuario:
            flash('Você precisa fazer login para acessar esta página.', 'error')
            return redirect(url_for('auth.login'))

        if usuario.perfil != 'admin':
            flash('Você não tem permissão para acessar esta página.', 'error')
            return redirect(url_for('index'))

        return f(*args, **kwargs)
    return decorated_function

def medico_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        usuario = get_usuario_atual()
        if not usuario:
            flash('Você precisa fazer login para acessar esta página.', 'error')
            return redirect(url_for('auth.login'))

        if usuario.perfil not in ['medico', 'admin']:
            flash('Você não tem permissão para acessar esta página.', 'error')
            return redirect(url_for('index'))

        return f(*args, **kwargs)
    return decorated_function

def validar_token_tv(token: str):
    try:
        usuario = Usuario.query.filter_by(
            token_tv=token,
            perfil='tv',
            ativo=True
        ).first()
        return usuario
    except Exception as e:
        print(f"Erro ao validar token TV: {e}")
        return None

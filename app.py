"""
Aplicação principal do Sistema de Gestão CLINED
Desenvolvido com Flask, SQLAlchemy e SQLite para máxima simplicidade
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, date
import os

# Importações dos módulos internos
from config import Config
from models.models import (db, Paciente, Profissional, Agendamento, Prontuario, AtendimentoHistorico,
                          Receituario, Laudo, Atestado, Recibo, SolicitacaoExame, MetaEmpresa,
                          Usuario, SessaoUsuario, LogAcesso)
from routes.agendamento import agendamento_bp
from routes.prontuario import prontuario_bp
from routes.financeiro import financeiro_bp
from routes.relatorios import relatorios_bp
from routes.documentos import documentos_bp
from routes.anexos import anexos_bp
from routes.chamados import chamados_bp
from routes.metas import metas_bp
from routes.auth import auth_bp
from routes.medico import medico_bp
from routes.admin import admin_bp
from utils.auth_helpers import get_usuario_atual, login_required, admin_required, hash_senha, gerar_token_tv

def create_app():
    """
    Factory function para criar e configurar a aplicação Flask
    Facilita testes e múltiplas instâncias da aplicação
    """
    app = Flask(__name__)
    
    # Aplicar configurações
    app.config.from_object(Config)
    
    # Inicializar extensões
    db.init_app(app)
    
    # Registrar blueprints (módulos)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(medico_bp, url_prefix='/medico')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(agendamento_bp, url_prefix='/agendamento')
    app.register_blueprint(prontuario_bp, url_prefix='/prontuario')
    app.register_blueprint(financeiro_bp, url_prefix='/financeiro')
    app.register_blueprint(relatorios_bp, url_prefix='/relatorios')
    app.register_blueprint(documentos_bp, url_prefix='/documentos')
    app.register_blueprint(anexos_bp, url_prefix='/anexos')
    app.register_blueprint(chamados_bp, url_prefix='/chamados')
    app.register_blueprint(metas_bp, url_prefix='/metas')
    
    # Criar tabelas do banco de dados se não existirem
    with app.app_context():
        db.create_all()
        criar_dados_iniciais()
        criar_usuarios_iniciais()
    
    # Tornar configuração e usuário disponíveis nos templates
    @app.context_processor
    def inject_config():
        return dict(config=Config, usuario_atual=get_usuario_atual())
    
    return app

def criar_dados_iniciais():
    """
    Cria dados iniciais para facilitar o uso do sistema
    Cadastra o Dr. Darlan Medeiros como único profissional
    """
    try:
        # Verificar se já existe o Dr. Darlan Medeiros cadastrado
        if Profissional.query.count() == 0:
            dr_darlan = Profissional(
                nome=Config.MEDICO_NOME,
                especialidade=Config.MEDICO_ESPECIALIDADE,
                registro_profissional=Config.MEDICO_CRM,
                telefone='(82) 99382-2424',
                email='contato@clined.com.br',
                horario_inicio=datetime.strptime(Config.HORARIO_ABERTURA, '%H:%M').time(),
                horario_fim=datetime.strptime(Config.HORARIO_FECHAMENTO, '%H:%M').time(),
                ativo=True
            )
            db.session.add(dr_darlan)
            db.session.commit()
            print(f"✅ {Config.MEDICO_NOME} cadastrado com sucesso!")
            
        # Criar paciente de exemplo se não houver nenhum
        if Paciente.query.count() == 0:
            paciente_exemplo = Paciente(
                nome='Paciente Exemplo',
                cpf='123.456.789-00',
                telefone='(11) 99999-9999',
                email='exemplo@email.com',
                data_nascimento=date(1990, 1, 1),
                endereco='Rua Exemplo, 123 - São Paulo, SP'
            )
            db.session.add(paciente_exemplo)
            db.session.commit()
            
            print("✅ Paciente exemplo criado com sucesso!")
            
    except Exception as e:
        print(f"⚠️  Erro ao criar dados iniciais: {str(e)}")
        db.session.rollback()

def criar_usuarios_iniciais():
    """
    Cria usuários iniciais no SQLite:
    - Admin padrão
    - Usuário médico vinculado ao Dr. Darlan Medeiros
    - Usuário TV para o painel
    """
    try:
        # Verificar se já existem usuários
        if Usuario.query.count() > 0:
            print("✅ Usuários já existem no sistema")
            return

        # Buscar o profissional Dr. Darlan Medeiros
        dr_darlan = Profissional.query.filter_by(ativo=True).first()
        profissional_id = dr_darlan.id if dr_darlan else None

        # Criar usuário administrador
        admin = Usuario(
            nome='Administrador',
            email='admin@clined.com.br',
            senha_hash=hash_senha('admin123'),
            perfil='admin',
            ativo=True
        )
        db.session.add(admin)
        print("✅ Usuário admin criado - Email: admin@clined.com.br | Senha: admin123")

        # Criar usuário médico
        medico = Usuario(
            nome='Dr. Darlan Medeiros',
            email='darlan@clined.com.br',
            senha_hash=hash_senha('medico123'),
            perfil='medico',
            ativo=True,
            profissional_id=profissional_id
        )
        db.session.add(medico)
        print("✅ Usuário médico criado - Email: darlan@clined.com.br | Senha: medico123")

        # Criar usuário TV
        token_tv = gerar_token_tv()
        tv = Usuario(
            nome='Painel de TV',
            email='tv@clined.com.br',
            senha_hash=hash_senha('tv123'),
            perfil='tv',
            ativo=True,
            token_tv=token_tv
        )
        db.session.add(tv)

        db.session.commit()

        print(f"✅ Usuário TV criado - Token: {token_tv}")
        print(f"   Acesse: http://localhost:5000/chamados/painel-tv?token={token_tv}")

    except Exception as e:
        print(f"⚠️  Erro ao criar usuários iniciais: {str(e)}")
        db.session.rollback()

# Criar a aplicação
app = create_app()

# Rotas principais da aplicação
@app.route('/')
@login_required
def index():
    """
    Página inicial (dashboard) do sistema
    Exibe resumo de informações importantes
    """
    try:
        # Buscar estatísticas básicas para o dashboard
        hoje = date.today()
        
        # Contar agendamentos de hoje por status
        agendamentos_hoje = Agendamento.query.filter(
            db.func.date(Agendamento.data_agendamento) == hoje
        ).count()
        
        em_espera = Agendamento.query.filter(
            db.func.date(Agendamento.data_agendamento) == hoje,
            Agendamento.status == 'em_espera'
        ).count()
        
        atendimentos = Agendamento.query.filter(
            db.func.date(Agendamento.data_agendamento) == hoje,
            Agendamento.status == 'em_atendimento'
        ).count()
        
        finalizados = Agendamento.query.filter(
            db.func.date(Agendamento.data_agendamento) == hoje,
            Agendamento.status == 'finalizado'
        ).count()
        
        # Renderizar template com estatísticas
        return render_template('index.html',
                             agendamentos_hoje=agendamentos_hoje,
                             em_espera=em_espera,
                             atendimentos=atendimentos,
                             finalizados=finalizados)
                             
    except Exception as e:
        flash(f'Erro ao carregar dashboard: {str(e)}', 'error')
        return render_template('index.html',
                             agendamentos_hoje=0,
                             em_espera=0,
                             atendimentos=0,
                             finalizados=0)

@app.errorhandler(404)
def not_found_error(error):
    """
    Página de erro 404 personalizada
    """
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """
    Página de erro 500 personalizada
    Faz rollback da sessão do banco em caso de erro
    """
    db.session.rollback()
    return render_template('errors/500.html'), 500

# Filtros customizados para templates Jinja2
@app.template_filter('datetime')
def datetime_filter(datetime_obj, format='%d/%m/%Y %H:%M'):
    """
    Filtro para formatação de data e hora nos templates
    Uso: {{ data_atendimento|datetime }}
    """
    if datetime_obj is None:
        return ""
    return datetime_obj.strftime(format)

@app.template_filter('date')
def date_filter(date_obj, format='%d/%m/%Y'):
    """
    Filtro para formatação de data nos templates
    Uso: {{ data_nascimento|date }}
    """
    if date_obj is None:
        return ""
    return date_obj.strftime(format)

@app.template_filter('cpf')
def cpf_filter(cpf_string):
    """
    Filtro para formatação de CPF nos templates
    Uso: {{ paciente.cpf|cpf }}
    """
    if not cpf_string:
        return ""
    # Remove caracteres não numéricos
    numbers = ''.join(filter(str.isdigit, cpf_string))
    if len(numbers) == 11:
        return f"{numbers[:3]}.{numbers[3:6]}.{numbers[6:9]}-{numbers[9:]}"
    return cpf_string

@app.template_filter('telefone')
def telefone_filter(telefone_string):
    """
    Filtro para formatação de telefone nos templates
    Uso: {{ paciente.telefone|telefone }}
    """
    if not telefone_string:
        return ""
    # Remove caracteres não numéricos
    numbers = ''.join(filter(str.isdigit, telefone_string))
    if len(numbers) == 11:
        return f"({numbers[:2]}) {numbers[2:7]}-{numbers[7:]}"
    elif len(numbers) == 10:
        return f"({numbers[:2]}) {numbers[2:6]}-{numbers[6:]}"
    return telefone_string

if __name__ == '__main__':
    """
    Execução da aplicação em modo de desenvolvimento
    """
    print("🏥 Iniciando Sistema de Gestão CLINED - Um novo conceito em saúde...")
    print("📋 CNPJ: 17505453/000172")
    print("📅 Sistema com módulos de Agendamento e Prontuário Eletrônico")
    print("🌐 Acesse: http://localhost:5000")
    print("📚 Documentação: README.md")
    print("-" * 60)
    
    # Executar aplicação Flask
    app.run(
        debug=Config.DEBUG,
        host='0.0.0.0',  # Permite acesso externo
        port=5000,
        threaded=True    # Permite múltiplas conexões simultâneas
    )
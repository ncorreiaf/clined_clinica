"""
Modelos de dados do Sistema CLINED
Utiliza SQLAlchemy para mapeamento objeto-relacional com SQLite
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Instância do SQLAlchemy (será inicializada no app.py)
db = SQLAlchemy()

class Paciente(db.Model):
    """
    Modelo para armazenar informações dos pacientes
    """
    __tablename__ = 'pacientes'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=True)
    telefone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100))
    data_nascimento = db.Column(db.Date)
    idade = db.Column(db.Integer)
    naturalidade = db.Column(db.String(100))
    estado_civil = db.Column(db.String(50))
    religiao = db.Column(db.String(50))
    profissao = db.Column(db.String(100))
    filiacao_pai = db.Column(db.String(100))
    filiacao_mae = db.Column(db.String(100))
    endereco = db.Column(db.Text)
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    data_cadastro = db.Column(db.DateTime, default=datetime.now)

    # Relacionamentos
    agendamentos = db.relationship('Agendamento', backref='paciente_ref', lazy=True)
    prontuarios = db.relationship('Prontuario', backref='paciente_ref', lazy=True)

class Profissional(db.Model):
    """
    Modelo para armazenar informações dos profissionais
    """
    __tablename__ = 'profissionais'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    especialidade = db.Column(db.String(50), nullable=False)
    registro_profissional = db.Column(db.String(20))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    horario_inicio = db.Column(db.Time)
    horario_fim = db.Column(db.Time)
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    agendamentos = db.relationship('Agendamento', backref='profissional_ref', lazy=True)

class Agendamento(db.Model):
    """
    Modelo para controle de agendamentos
    """
    __tablename__ = 'agendamentos'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissionais.id'), nullable=False)
    data_agendamento = db.Column(db.DateTime, nullable=False)
    servico = db.Column(db.String(100), nullable=False)
    observacoes = db.Column(db.Text)
    status = db.Column(db.String(20), default='agendado')
    # Status possíveis: agendado, em_espera, em_atendimento, finalizado, faltou
    data_checkin = db.Column(db.DateTime)
    data_criacao = db.Column(db.DateTime, default=datetime.now)

class Prontuario(db.Model):
    """
    Modelo para prontuários eletrônicos
    """
    __tablename__ = 'prontuarios'

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    agendamento_id = db.Column(db.Integer, db.ForeignKey('agendamentos.id'))
    data_atendimento = db.Column(db.DateTime, default=datetime.now)
    especialidade = db.Column(db.String(50))
    queixa_principal = db.Column(db.Text)
    historia_doenca = db.Column(db.Text)
    exame_fisico = db.Column(db.Text)
    diagnostico = db.Column(db.Text)
    prescricao = db.Column(db.Text)
    observacoes = db.Column(db.Text)
    profissional_nome = db.Column(db.String(100))

    # Campos para documentos
    exames_solicitados = db.Column(db.Text)
    indicacao_clinica = db.Column(db.Text)

    # Relacionamentos
    historico = db.relationship('AtendimentoHistorico', backref='prontuario_ref', lazy=True)

class AtendimentoHistorico(db.Model):
    """
    Modelo para histórico de atendimentos
    """
    __tablename__ = 'atendimento_historico'
    
    id = db.Column(db.Integer, primary_key=True)
    prontuario_id = db.Column(db.Integer, db.ForeignKey('prontuarios.id'), nullable=False)
    data_atendimento = db.Column(db.DateTime, default=datetime.now)
    tipo_atendimento = db.Column(db.String(50))  # consulta, exame, terapia
    descricao = db.Column(db.Text)
    profissional = db.Column(db.String(100))
    
class SolicitacaoExame(db.Model):
    """
    Modelo para solicitações de exames
    """
    __tablename__ = 'solicitacao_exames'

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    agendamento_id = db.Column(db.Integer, db.ForeignKey('agendamentos.id'))
    prontuario_id = db.Column(db.Integer, db.ForeignKey('prontuarios.id'))
    tipo_exame = db.Column(db.String(100), nullable=False)
    observacoes = db.Column(db.Text)
    indicacao_clinica = db.Column(db.Text)
    status = db.Column(db.String(20), default='solicitado')
    data_solicitacao = db.Column(db.DateTime, default=datetime.now)
    data_realizacao = db.Column(db.DateTime)

    paciente_exame = db.relationship('Paciente', backref='exames_solicitados')

class Receituario(db.Model):
    """
    Modelo para receituários médicos
    """
    __tablename__ = 'receituarios'

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    prontuario_id = db.Column(db.Integer, db.ForeignKey('prontuarios.id'))
    medicamentos = db.Column(db.Text, nullable=False)
    posologia = db.Column(db.Text)
    observacoes = db.Column(db.Text)
    data_emissao = db.Column(db.DateTime, default=datetime.now)
    validade = db.Column(db.Date)

    paciente_receita = db.relationship('Paciente', backref='receituarios')

class Laudo(db.Model):
    """
    Modelo para laudos médicos e relatórios
    """
    __tablename__ = 'laudos'

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    prontuario_id = db.Column(db.Integer, db.ForeignKey('prontuarios.id'))
    tipo_exame = db.Column(db.String(100))
    titulo = db.Column(db.String(200), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    conclusao = db.Column(db.Text)
    data_emissao = db.Column(db.DateTime, default=datetime.now)

    paciente_laudo = db.relationship('Paciente', backref='laudos')

class Atestado(db.Model):
    """
    Modelo para atestados médicos
    """
    __tablename__ = 'atestados'

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    prontuario_id = db.Column(db.Integer, db.ForeignKey('prontuarios.id'))
    cid = db.Column(db.String(10))
    dias_afastamento = db.Column(db.Integer)
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date)
    observacoes = db.Column(db.Text)
    data_emissao = db.Column(db.DateTime, default=datetime.now)

    paciente_atestado = db.relationship('Paciente', backref='atestados')

class Recibo(db.Model):
    """
    Modelo para recibos de pagamento
    """
    __tablename__ = 'recibos'

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    agendamento_id = db.Column(db.Integer, db.ForeignKey('agendamentos.id'))
    descricao_servico = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    forma_pagamento = db.Column(db.String(50))
    data_emissao = db.Column(db.DateTime, default=datetime.now)
    numero_recibo = db.Column(db.String(20), unique=True)

    paciente_recibo = db.relationship('Paciente', backref='recibos')
    agendamento_recibo = db.relationship('Agendamento', backref='recibo', uselist=False)

# ========== MÓDULO 3 - FINANCEIRO ==========

class ContaReceber(db.Model):
    """
    Modelo para contas a receber
    """
    __tablename__ = 'contas_receber'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    agendamento_id = db.Column(db.Integer, db.ForeignKey('agendamentos.id'))
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    data_pagamento = db.Column(db.Date)
    status = db.Column(db.String(20), default='pendente')  # pendente, pago, vencido
    forma_pagamento = db.Column(db.String(50))  # dinheiro, cartao, pix, etc
    observacoes = db.Column(db.Text)
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    
    # Relacionamentos
    paciente_conta = db.relationship('Paciente', backref='contas_receber')
    agendamento_conta = db.relationship('Agendamento', backref='conta_receber')

class ContaPagar(db.Model):
    """
    Modelo para contas a pagar
    """
    __tablename__ = 'contas_pagar'

    id = db.Column(db.Integer, primary_key=True)
    fornecedor = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    data_pagamento = db.Column(db.Date)
    status = db.Column(db.String(20), default='pendente')  # pendente, pago, vencido
    categoria = db.Column(db.String(50))  # aluguel, material, salario, etc
    centro_custo = db.Column(db.String(50))
    forma_pagamento = db.Column(db.String(50))
    observacoes = db.Column(db.Text)
    data_criacao = db.Column(db.DateTime, default=datetime.now)

class FluxoCaixa(db.Model):
    """
    Modelo para controle de fluxo de caixa
    """
    __tablename__ = 'fluxo_caixa'
    
    id = db.Column(db.Integer, primary_key=True)
    data_movimento = db.Column(db.Date, nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # entrada, saida
    categoria = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    forma_pagamento = db.Column(db.String(50))
    conta_receber_id = db.Column(db.Integer, db.ForeignKey('contas_receber.id'))
    conta_pagar_id = db.Column(db.Integer, db.ForeignKey('contas_pagar.id'))
    recepcionista = db.Column(db.String(100))
    data_criacao = db.Column(db.DateTime, default=datetime.now)

class MetaEmpresa(db.Model):
    """
    Modelo para metas da empresa (faturamento, atendimentos, novos clientes)
    """
    __tablename__ = 'metas_empresa'

    id = db.Column(db.Integer, primary_key=True)
    mes = db.Column(db.Integer, nullable=False)  # 1 a 12
    ano = db.Column(db.Integer, nullable=False)
    meta_faturamento = db.Column(db.Numeric(10, 2), default=0)
    meta_atendimentos = db.Column(db.Integer, default=0)
    meta_novos_clientes = db.Column(db.Integer, default=0)
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    data_atualizacao = db.Column(db.DateTime, onupdate=datetime.now)

    # Constraint única para mes/ano
    __table_args__ = (db.UniqueConstraint('mes', 'ano', name='unique_mes_ano'),)

# ========== MÓDULO 4 - RELATÓRIOS E INDICADORES ==========

class AvaliacaoSatisfacao(db.Model):
    """
    Modelo para avaliações de satisfação (NPS)
    """
    __tablename__ = 'avaliacao_satisfacao'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    agendamento_id = db.Column(db.Integer, db.ForeignKey('agendamentos.id'))
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissionais.id'))
    nota_nps = db.Column(db.Integer, nullable=False)  # 0 a 10
    comentario = db.Column(db.Text)
    data_avaliacao = db.Column(db.DateTime, default=datetime.now)
    
    # Relacionamentos
    paciente_avaliacao = db.relationship('Paciente', backref='avaliacoes')
    agendamento_avaliacao = db.relationship('Agendamento', backref='avaliacao')
    profissional_avaliacao = db.relationship('Profissional', backref='avaliacoes')

class LogAuditoria(db.Model):
    """
    Modelo para log de auditoria interna
    """
    __tablename__ = 'log_auditoria'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(100), nullable=False)
    acao = db.Column(db.String(100), nullable=False)
    tabela = db.Column(db.String(50), nullable=False)
    registro_id = db.Column(db.Integer)
    dados_anteriores = db.Column(db.Text)
    dados_novos = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    data_acao = db.Column(db.DateTime, default=datetime.now)

class AlertaAutomatico(db.Model):
    """
    Modelo para alertas automáticos do sistema
    """
    __tablename__ = 'alerta_automatico'

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)  # vencimento, meta, anomalia
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    prioridade = db.Column(db.String(20), default='media')  # baixa, media, alta
    status = db.Column(db.String(20), default='ativo')  # ativo, resolvido, ignorado
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    data_resolucao = db.Column(db.DateTime)

class AnexoProntuario(db.Model):
    """
    Modelo para anexos de arquivos nos prontuários
    """
    __tablename__ = 'anexos_prontuario'

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    prontuario_id = db.Column(db.Integer, db.ForeignKey('prontuarios.id'))
    nome_arquivo = db.Column(db.String(255), nullable=False)
    nome_original = db.Column(db.String(255), nullable=False)
    tipo_arquivo = db.Column(db.String(100))  # application/pdf, image/jpeg, etc
    tamanho = db.Column(db.Integer)  # tamanho em bytes
    descricao = db.Column(db.Text)
    data_upload = db.Column(db.DateTime, default=datetime.now)
    usuario_upload = db.Column(db.String(100))  # quem fez o upload

    # Relacionamentos
    paciente_anexo = db.relationship('Paciente', backref='anexos')
    prontuario_anexo = db.relationship('Prontuario', backref='anexos')

# ========== SISTEMA DE AUTENTICAÇÃO ==========

class Usuario(db.Model):
    """
    Modelo para usuários do sistema com controle de acesso
    """
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    perfil = db.Column(db.String(20), nullable=False)  # admin, medico, tv
    ativo = db.Column(db.Boolean, default=True)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissionais.id'))
    ultimo_acesso = db.Column(db.DateTime)
    token_tv = db.Column(db.String(100), unique=True)
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    data_atualizacao = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relacionamentos
    profissional = db.relationship('Profissional', backref='usuario')
    sessoes = db.relationship('SessaoUsuario', backref='usuario', lazy=True, cascade='all, delete-orphan')
    logs = db.relationship('LogAcesso', backref='usuario', lazy=True)

class SessaoUsuario(db.Model):
    """
    Modelo para controle de sessões ativas dos usuários
    """
    __tablename__ = 'sessoes_usuario'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    token_sessao = db.Column(db.String(100), unique=True, nullable=False)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.Text)
    expira_em = db.Column(db.DateTime, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.now)

class LogAcesso(db.Model):
    """
    Modelo para logs de auditoria de acesso ao sistema
    """
    __tablename__ = 'logs_acesso'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    acao = db.Column(db.String(50), nullable=False)  # login, logout, acesso_negado, senha_alterada, etc
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.Text)
    detalhes = db.Column(db.Text)  # JSON string com informações adicionais
    sucesso = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.now)

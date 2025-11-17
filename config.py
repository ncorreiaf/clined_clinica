# Configurações do Sistema CLINED
import os

class Config:
    """
    Classe de configuração principal do sistema.
    Centraliza todas as configurações para facilitar manutenção.
    """

    # Configuração do banco de dados
    # Em produção, usa DATABASE_URL (PostgreSQL do Render)
    # Em desenvolvimento, usa SQLite local
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///database.db')

    # Fix para PostgreSQL no SQLAlchemy 1.4+ (Render usa postgres://, precisa ser postgresql://)
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Chave secreta para sessões
    SECRET_KEY = os.environ.get('SECRET_KEY', 'clined-secret-key-2023')

    # Configurações da aplicação
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

    # Nome da clínica
    CLINIC_NAME = "CLINED - Um novo conceito em saúde"

    # CNPJ da clínica
    CLINIC_CNPJ = "17505453/000172"

    # Médico responsável
    MEDICO_NOME = "Dr. Darlan Medeiros"
    MEDICO_CRM = "CRM: 2165 - AL"
    MEDICO_ESPECIALIDADE = "Psiquiatria"

    # Horários de funcionamento
    HORARIO_ABERTURA = "08:00"
    HORARIO_FECHAMENTO = "18:00"

    # Serviços disponíveis
    SERVICOS_DISPONIVEIS = [
        'Consulta Médica',
        'Eletroencefalograma',
        'Eletrocardiograma',
        'Mapa Holter',
        'Ecocardiograma',
        'Ultrassonografia'
    ]

    # Status de atendimento (cores para interface)
    STATUS_CORES = {
        'agendado': 'blue',
        'em_espera': 'orange',
        'em_atendimento': 'green',
        'finalizado': 'gray',
        'faltou': 'red'
    }
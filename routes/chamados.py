"""
Rotas do Módulo de Chamados (Painel de TV)
Exibe em tempo real os atendimentos para visualização no consultório
"""

from flask import Blueprint, render_template, jsonify, request, abort, session
from models.models import db, Agendamento, Paciente, Profissional
from utils.auth_helpers import validar_token_tv, get_usuario_atual
from datetime import datetime, date

chamados_bp = Blueprint('chamados', __name__)

@chamados_bp.route('/painel-tv')
def painel_tv():
    """
    Exibe o painel de TV com os atendimentos do dia
    Aceita duas formas de acesso:
    1. Usuario logado no sistema (qualquer perfil)
    2. Token de acesso via URL (para TVs fisicas)
    """
    usuario_logado = get_usuario_atual()

    if usuario_logado:
        return render_template('chamados/painel_tv.html')

    token = request.args.get('token')

    if token:
        usuario_tv = validar_token_tv(token)
        if usuario_tv:
            return render_template('chamados/painel_tv.html')

    abort(403, description="Acesso negado. Faça login ou forneça um token válido")

@chamados_bp.route('/api/atendimentos-atual')
def api_atendimentos():
    """
    API para buscar atendimentos em tempo real
    Retorna o atendimento atual e os próximos 3
    """
    # Buscar atendimento em andamento (sem filtro de data)
    atendimento_atual = Agendamento.query.filter(
        Agendamento.status == 'em_atendimento'
    ).first()

    # Buscar próximos atendimentos (agendados ou em espera)
    proximos = Agendamento.query.filter(
        db.or_(
            Agendamento.status == 'agendado',
            Agendamento.status == 'em_espera'
        )
    ).order_by(Agendamento.data_agendamento).limit(3).all()

    # Buscar informações do profissional
    profissional = Profissional.query.filter_by(ativo=True).first()

    resultado = {
        'atual': None,
        'proximos': [],
        'profissional': {
            'nome': profissional.nome if profissional else 'N/A',
            'especialidade': profissional.especialidade if profissional else 'N/A',
            'crm': profissional.registro_profissional if profissional else 'N/A'
        }
    }

    # Formatar atendimento atual
    if atendimento_atual:
        resultado['atual'] = {
            'paciente': atendimento_atual.paciente_ref.nome,
            'servico': atendimento_atual.servico,
            'horario': atendimento_atual.data_agendamento.strftime('%H:%M'),
            'status': 'Em Atendimento'
        }

    # Formatar próximos atendimentos
    for agendamento in proximos:
        resultado['proximos'].append({
            'paciente': agendamento.paciente_ref.nome,
            'servico': agendamento.servico,
            'horario': agendamento.data_agendamento.strftime('%H:%M'),
            'status': 'Aguardando' if agendamento.status == 'em_espera' else 'Agendado'
        })

    return jsonify(resultado)

@chamados_bp.route('/api/estatisticas-dia')
def api_estatisticas():
    """
    API para estatísticas do dia
    """
    # Contar todos independente de data por enquanto
    total_dia = Agendamento.query.count()

    atendidos = Agendamento.query.filter(
        Agendamento.status == 'finalizado'
    ).count()

    em_espera = Agendamento.query.filter(
        db.or_(
            Agendamento.status == 'agendado',
            Agendamento.status == 'em_espera'
        )
    ).count()

    return jsonify({
        'total': total_dia,
        'atendidos': atendidos,
        'em_espera': em_espera
    })

@chamados_bp.route('/api/debug-agendamentos')
def debug_agendamentos():
    """
    Debug: Ver todos os agendamentos e seus status
    """
    agendamentos = Agendamento.query.order_by(Agendamento.data_hora.desc()).limit(10).all()

    resultado = []
    for ag in agendamentos:
        resultado.append({
            'id': ag.id,
            'paciente': ag.paciente_ref.nome,
            'data_hora': ag.data_agendamento.strftime('%Y-%m-%d %H:%M:%S'),
            'status': ag.status,
            'servico': ag.servico
        })

    return jsonify({
        'agendamentos': resultado,
        'total': len(resultado),
        'hora_servidor': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

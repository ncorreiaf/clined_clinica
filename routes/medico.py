from flask import Blueprint, render_template, redirect, url_for, flash
from utils.auth_helpers import medico_required, get_usuario_atual
from models.models import db, Agendamento, Paciente, Prontuario
from datetime import datetime, date

medico_bp = Blueprint('medico', __name__)

@medico_bp.route('/dashboard')
@medico_required
def dashboard():
    usuario = get_usuario_atual()

    try:
        hoje = date.today()

        agendamentos_hoje = Agendamento.query.filter(
            db.func.date(Agendamento.data_agendamento) == hoje
        ).order_by(Agendamento.data_agendamento).all()

        em_espera = [a for a in agendamentos_hoje if a.status == 'em_espera']
        em_atendimento = [a for a in agendamentos_hoje if a.status == 'em_atendimento']
        finalizados = [a for a in agendamentos_hoje if a.status == 'finalizado']

        proximo_paciente = None
        if em_espera:
            proximo_paciente = em_espera[0]
        elif not em_atendimento and agendamentos_hoje:
            agendados = [a for a in agendamentos_hoje if a.status == 'agendado']
            if agendados:
                proximo_paciente = agendados[0]

        total_pacientes = Paciente.query.count()
        total_prontuarios = Prontuario.query.count()

        return render_template('medico/dashboard.html',
                             usuario=usuario,
                             agendamentos_hoje=agendamentos_hoje,
                             em_espera=em_espera,
                             em_atendimento=em_atendimento,
                             finalizados=finalizados,
                             proximo_paciente=proximo_paciente,
                             total_pacientes=total_pacientes,
                             total_prontuarios=total_prontuarios)

    except Exception as e:
        flash(f'Erro ao carregar dashboard: {str(e)}', 'error')
        return render_template('medico/dashboard.html',
                             usuario=usuario,
                             agendamentos_hoje=[],
                             em_espera=[],
                             em_atendimento=[],
                             finalizados=[],
                             proximo_paciente=None,
                             total_pacientes=0,
                             total_prontuarios=0)

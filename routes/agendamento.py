"""
Rotas do Módulo 1 - Agendamento e Atendimento
Gerencia todas as funcionalidades relacionadas a agendamentos
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.models import db, Agendamento, Paciente, Profissional, SolicitacaoExame
from config import Config
from datetime import datetime
from utils.auth_helpers import login_required

# Criação do Blueprint para agendamentos
agendamento_bp = Blueprint('agendamento', __name__)

@agendamento_bp.route('/horarios-disponiveis')
def horarios_disponiveis():
    """
    API para retornar horários disponíveis para uma data específica
    Horário: 08:00 às 18:00, intervalos de 30 minutos
    """
    data_str = request.args.get('data', '')

    if not data_str:
        return jsonify({'error': 'Data não fornecida'}), 400

    try:
        data_selecionada = datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Data inválida'}), 400

    # Gerar todos os horários possíveis (08:00 às 18:00, intervalos de 30min)
    horarios_possiveis = []
    for hora in range(8, 18):
        for minuto in [0, 30]:
            horarios_possiveis.append(f"{hora:02d}:{minuto:02d}")

    # Buscar agendamentos existentes para a data
    agendamentos_dia = Agendamento.query.filter(
        db.func.date(Agendamento.data_agendamento) == data_selecionada
    ).all()

    # Marcar horários ocupados
    horarios_ocupados = set()
    for ag in agendamentos_dia:
        horario = ag.data_agendamento.strftime('%H:%M')
        horarios_ocupados.add(horario)

    # Criar lista de horários com disponibilidade
    resultado = []
    for horario in horarios_possiveis:
        resultado.append({
            'horario': horario,
            'disponivel': horario not in horarios_ocupados
        })

    return jsonify({'horarios': resultado})

@agendamento_bp.route('/buscar-paciente')
def buscar_paciente():
    """
    API para buscar pacientes por nome ou CPF
    """
    termo = request.args.get('termo', '').strip()

    if len(termo) < 3:
        return jsonify({'pacientes': []})

    # Buscar por nome ou CPF
    pacientes = Paciente.query.filter(
        db.or_(
            Paciente.nome.ilike(f'%{termo}%'),
            Paciente.cpf.ilike(f'%{termo}%')
        )
    ).limit(10).all()

    resultado = []
    for p in pacientes:
        resultado.append({
            'id': p.id,
            'nome': p.nome,
            'cpf': p.cpf,
            'telefone': p.telefone or '',
            'email': p.email or ''
        })

    return jsonify({'pacientes': resultado})

@agendamento_bp.route('/agendar', methods=['GET', 'POST'])
@login_required
def agendar():
    """
    Rota para criar novos agendamentos
    GET: Exibe o formulário de agendamento
    POST: Processa e salva o novo agendamento
    """
    if request.method == 'POST':
        try:
            # Coleta dados do formulário
            nome_paciente = request.form['nome_paciente']
            cpf_paciente = request.form['cpf_paciente']
            telefone = request.form['telefone']
            email = request.form.get('email', '')
            data_agendamento = datetime.strptime(request.form['data_agendamento'], '%Y-%m-%dT%H:%M')
            servico = request.form['servico']
            observacoes = request.form.get('observacoes', '')

            # Buscar o Dr. Darlan Medeiros (único profissional)
            dr_darlan = Profissional.query.filter_by(ativo=True).first()
            if not dr_darlan:
                flash('Erro: Profissional não encontrado no sistema!', 'error')
                return redirect(url_for('agendamento.agendar'))

            # Verifica se o paciente já existe, se não, cria um novo
            paciente = Paciente.query.filter_by(cpf=cpf_paciente).first()
            if not paciente:
                paciente = Paciente(
                    nome=nome_paciente,
                    cpf=cpf_paciente,
                    telefone=telefone,
                    email=email
                )
                db.session.add(paciente)
                db.session.flush()
            else:
                # Atualiza dados do paciente se mudou
                paciente.nome = nome_paciente
                paciente.telefone = telefone
                if email:
                    paciente.email = email

            # Cria o novo agendamento
            novo_agendamento = Agendamento(
                paciente_id=paciente.id,
                profissional_id=dr_darlan.id,
                data_agendamento=data_agendamento,
                servico=servico,
                observacoes=observacoes
            )

            db.session.add(novo_agendamento)
            db.session.commit()

            flash('Agendamento realizado com sucesso!', 'success')
            return redirect(url_for('agendamento.lista_agendamentos'))

        except Exception as e:
            flash(f'Erro ao realizar agendamento: {str(e)}', 'error')
            db.session.rollback()

    # Lista de serviços disponíveis
    servicos = Config.SERVICOS_DISPONIVEIS
    return render_template('agendamento/agendar.html', servicos=servicos)

@agendamento_bp.route('/lista')
@login_required
def lista_agendamentos():
    """
    Rota para exibir lista de agendamentos
    Mostra agendamentos do dia atual por padrão
    """
    data_filtro = request.args.get('data', datetime.now().strftime('%Y-%m-%d'))
    
    # Busca agendamentos da data especificada
    agendamentos = db.session.query(Agendamento, Paciente, Profissional).join(
        Paciente, Agendamento.paciente_id == Paciente.id
    ).join(
        Profissional, Agendamento.profissional_id == Profissional.id
    ).filter(
        db.func.date(Agendamento.data_agendamento) == data_filtro
    ).order_by(Agendamento.data_agendamento).all()
    
    return render_template('agendamento/lista.html', 
                         agendamentos=agendamentos, 
                         data_filtro=data_filtro)

@agendamento_bp.route('/fila-espera')
@login_required
def fila_espera():
    """
    Rota para gerenciar a fila de espera
    Mostra pacientes em diferentes status de atendimento
    """
    # Busca agendamentos do dia atual com diferentes status
    hoje = datetime.now().date()
    
    agendamentos_hoje = db.session.query(Agendamento, Paciente, Profissional).join(
        Paciente, Agendamento.paciente_id == Paciente.id
    ).join(
        Profissional, Agendamento.profissional_id == Profissional.id
    ).filter(
        db.func.date(Agendamento.data_agendamento) == hoje
    ).order_by(Agendamento.data_agendamento).all()
    
    return render_template('agendamento/fila_espera.html', agendamentos=agendamentos_hoje)

@agendamento_bp.route('/checkin/<int:agendamento_id>')
@login_required
def checkin(agendamento_id):
    """
    Rota para realizar check-in do paciente
    Atualiza status do agendamento para 'em_espera'
    """
    try:
        agendamento = Agendamento.query.get_or_404(agendamento_id)
        agendamento.status = 'em_espera'
        agendamento.data_checkin = datetime.now()
        
        db.session.commit()
        flash('Check-in realizado com sucesso!', 'success')
        
    except Exception as e:
        flash(f'Erro no check-in: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('agendamento.fila_espera'))

@agendamento_bp.route('/atualizar-status/<int:agendamento_id>/<status>')
@login_required
def atualizar_status(agendamento_id, status):
    """
    Rota para atualizar status do agendamento
    Status possíveis: agendado, em_espera, em_atendimento, finalizado, faltou
    """
    try:
        agendamento = Agendamento.query.get_or_404(agendamento_id)
        agendamento.status = status
        
        db.session.commit()
        flash(f'Status atualizado para: {status}', 'success')
        
    except Exception as e:
        flash(f'Erro ao atualizar status: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('agendamento.fila_espera'))


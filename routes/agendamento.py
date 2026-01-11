"""
Rotas do Módulo 1 - Agendamento e Atendimento
Gerencia todas as funcionalidades relacionadas a agendamentos
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.models import db, Agendamento, Paciente, Profissional, SolicitacaoExame
from config import Config
from datetime import datetime
from utils.auth_helpers import login_required, agendamento_required

# Criação do Blueprint para agendamentos
agendamento_bp = Blueprint('agendamento', __name__)

@agendamento_bp.route('/horarios-disponiveis')
def horarios_disponiveis():
    """
    API para retornar horários disponíveis para uma data específica
    Horário: 08:00 às 20:00, intervalos de 30 minutos
    Cada serviço tem sua própria grade (múltiplos serviços no mesmo horário são permitidos)
    """
    data_str = request.args.get('data', '')
    servico = request.args.get('servico', '').strip()

    if not data_str:
        return jsonify({'error': 'Data não fornecida'}), 400

    if not servico:
        return jsonify({'error': 'Serviço não fornecido'}), 400

    try:
        data_selecionada = datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Data inválida'}), 400

    # Gerar todos os horários possíveis (08:00 às 20:00, intervalos de 30min)
    horarios_possiveis = []
    for hora in range(8, 20):
        for minuto in [0, 30]:
            horarios_possiveis.append(f"{hora:02d}:{minuto:02d}")

    # Buscar agendamentos existentes para a data E serviço específico
    agendamentos_dia = Agendamento.query.filter(
        db.func.date(Agendamento.data_agendamento) == data_selecionada,
        Agendamento.servico == servico
    ).all()

    # Marcar horários ocupados (apenas para o serviço específico)
    horarios_ocupados = set()
    for ag in agendamentos_dia:
        horario = ag.data_agendamento.strftime('%H:%M')
        horarios_ocupados.add(horario)

    # Criar lista de horários com disponibilidade
    resultado = []
    for horario in horarios_possiveis:
        resultado.append({
            'horario': horario,
            'disponivel': horario not in horarios_ocupados,
            'motivo': 'Ocupado' if horario in horarios_ocupados else ''
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
            # Coleta dados do formulário com TRIM
            nome_paciente = request.form['nome_paciente'].strip()
            cpf_paciente = request.form.get('cpf_paciente', '').strip()
            telefone = request.form['telefone'].strip()
            email = request.form.get('email', '').strip()
            data_agendamento = datetime.strptime(request.form['data_agendamento'], '%Y-%m-%dT%H:%M')
            servico = request.form['servico'].strip()
            observacoes = request.form.get('observacoes', '').strip()

            print("\n" + "="*60)
            print("📋 NOVO CADASTRO/AGENDAMENTO")
            print("="*60)
            print(f"Nome: {nome_paciente}")
            print(f"CPF: {cpf_paciente if cpf_paciente else '(não informado)'}")
            print(f"Telefone: {telefone}")
            print(f"Email: {email if email else '(não informado)'}")

            # Validação: verificar se já existe agendamento para o mesmo serviço no mesmo horário
            agendamento_existente = Agendamento.query.filter(
                Agendamento.data_agendamento == data_agendamento,
                Agendamento.servico == servico
            ).first()

            if agendamento_existente:
                flash(f'Já existe um agendamento de {servico} para este horário!', 'error')
                return redirect(url_for('agendamento.agendar'))

            # Buscar o Dr. Darlan Medeiros (único profissional)
            dr_darlan = Profissional.query.filter_by(ativo=True).first()
            if not dr_darlan:
                flash('Erro: Profissional não encontrado no sistema!', 'error')
                return redirect(url_for('agendamento.agendar'))

            # Coletar dados adicionais do paciente
            data_nascimento_str = request.form.get('data_nascimento', '').strip()
            data_nascimento = datetime.strptime(data_nascimento_str, '%Y-%m-%d').date() if data_nascimento_str else None
            idade = int(request.form.get('idade', 0)) if request.form.get('idade') else None
            naturalidade = request.form.get('naturalidade', '').strip()
            estado_civil = request.form.get('estado_civil', '').strip()
            religiao = request.form.get('religiao', '').strip()
            profissao = request.form.get('profissao', '').strip()
            filiacao_mae = request.form.get('filiacao_mae', '').strip()
            filiacao_pai = request.form.get('filiacao_pai', '').strip()
            endereco = request.form.get('endereco', '').strip()
            bairro = request.form.get('bairro', '').strip()
            cidade = request.form.get('cidade', '').strip()

            # Mostrar todos os pacientes existentes no banco PARA DEBUG
            total_pacientes = Paciente.query.count()
            print(f"\n📊 Total de pacientes no banco ANTES: {total_pacientes}")
            if total_pacientes > 0 and total_pacientes <= 10:
                print("\n👥 Lista de pacientes existentes:")
                todos = Paciente.query.all()
                for p in todos:
                    print(f"   ID={p.id}, Nome={p.nome}, CPF={p.cpf or '(sem CPF)'}, Tel={p.telefone}")

            # Verifica se o paciente já existe
            # IMPORTANTE: Busca inteligente para evitar duplicatas
            paciente = None

            if cpf_paciente and cpf_paciente.strip():
                # Se CPF foi fornecido, busca por CPF
                paciente = Paciente.query.filter_by(cpf=cpf_paciente).first()
                print(f"\n🔍 Buscando por CPF: {cpf_paciente}")
                print(f"   Resultado: {'ENCONTRADO ID=' + str(paciente.id) if paciente else 'NÃO ENCONTRADO - CRIANDO NOVO'}")
            else:
                # Se CPF NÃO foi fornecido, busca por Nome + Telefone
                paciente = Paciente.query.filter_by(
                    nome=nome_paciente,
                    telefone=telefone
                ).first()
                print(f"\n🔍 Buscando por Nome+Telefone: {nome_paciente} / {telefone}")
                print(f"   Resultado: {'ENCONTRADO ID=' + str(paciente.id) if paciente else 'NÃO ENCONTRADO - CRIANDO NOVO'}")

            if not paciente:
                # CRIAR NOVO PACIENTE
                print(f"\n➕ CRIANDO NOVO PACIENTE")
                paciente = Paciente(
                    nome=nome_paciente,
                    cpf=cpf_paciente if cpf_paciente and cpf_paciente.strip() else None,
                    telefone=telefone,
                    email=email,
                    data_nascimento=data_nascimento,
                    idade=idade,
                    naturalidade=naturalidade,
                    estado_civil=estado_civil,
                    religiao=religiao,
                    profissao=profissao,
                    filiacao_mae=filiacao_mae,
                    filiacao_pai=filiacao_pai,
                    endereco=endereco,
                    bairro=bairro,
                    cidade=cidade
                )
                db.session.add(paciente)
                db.session.flush()
                print(f"✅ NOVO PACIENTE CRIADO: ID={paciente.id}, Nome={paciente.nome}, CPF={paciente.cpf or '(sem CPF)'}")
            else:
                # ATUALIZAR PACIENTE EXISTENTE
                print(f"\n✏️  ATUALIZANDO PACIENTE EXISTENTE: ID={paciente.id}")
                print(f"   Nome antigo: {paciente.nome} → Novo: {nome_paciente}")
                paciente.nome = nome_paciente
                paciente.telefone = telefone
                if email:
                    paciente.email = email
                if data_nascimento:
                    paciente.data_nascimento = data_nascimento
                if idade is not None:
                    paciente.idade = idade
                if naturalidade:
                    paciente.naturalidade = naturalidade
                if estado_civil:
                    paciente.estado_civil = estado_civil
                if religiao:
                    paciente.religiao = religiao
                if profissao:
                    paciente.profissao = profissao
                if filiacao_mae:
                    paciente.filiacao_mae = filiacao_mae
                if filiacao_pai:
                    paciente.filiacao_pai = filiacao_pai
                if endereco:
                    paciente.endereco = endereco
                if bairro:
                    paciente.bairro = bairro
                if cidade:
                    paciente.cidade = cidade

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

            # Mostrar estado final do banco
            total_pacientes_depois = Paciente.query.count()
            print(f"\n📊 Total de pacientes no banco DEPOIS: {total_pacientes_depois}")
            if total_pacientes_depois <= 10:
                print("\n👥 Lista FINAL de pacientes:")
                todos = Paciente.query.all()
                for p in todos:
                    print(f"   ID={p.id}, Nome={p.nome}, CPF={p.cpf or '(sem CPF)'}, Tel={p.telefone}")
            print("="*60 + "\n")

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
@agendamento_required
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
@agendamento_required
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


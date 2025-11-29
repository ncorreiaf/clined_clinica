"""
Rotas para Documentos Médicos
Gerencia receituários, laudos, atestados e recibos
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.models import db, Paciente, Prontuario, Receituario, Laudo, Atestado, Recibo, Agendamento
from config import Config
from datetime import datetime, date, timedelta

documentos_bp = Blueprint('documentos', __name__)

@documentos_bp.route('/receituario/<int:prontuario_id>')
def gerar_receituario(prontuario_id):
    """Gera receituário médico"""
    prontuario = Prontuario.query.get_or_404(prontuario_id)
    paciente = Paciente.query.get_or_404(prontuario.paciente_id)

    return render_template('documentos/receituario.html',
                         prontuario=prontuario,
                         paciente=paciente,
                         medico=Config.MEDICO_NOME,
                         crm=Config.MEDICO_CRM)

@documentos_bp.route('/receituario/<int:prontuario_id>/salvar', methods=['POST'])
def salvar_receituario(prontuario_id):
    """Salva receituário no banco de dados"""
    try:
        prontuario = Prontuario.query.get_or_404(prontuario_id)

        receituario = Receituario(
            paciente_id=prontuario.paciente_id,
            prontuario_id=prontuario_id,
            medicamentos=request.form.get('medicamentos', '').strip(),
            posologia=request.form.get('posologia', '').strip(),
            observacoes=request.form.get('observacoes', '').strip(),
            validade=datetime.now().date() + timedelta(days=30)
        )

        db.session.add(receituario)
        db.session.commit()

        flash('Receituário salvo com sucesso!', 'success')
        return redirect(url_for('documentos.gerar_receituario', prontuario_id=prontuario_id))
    except Exception as e:
        flash(f'Erro ao salvar receituário: {str(e)}', 'error')
        return redirect(url_for('prontuario.ver_prontuario', paciente_id=prontuario.paciente_id))

@documentos_bp.route('/laudo/<int:prontuario_id>')
def gerar_laudo(prontuario_id):
    """Gera laudo médico"""
    prontuario = Prontuario.query.get_or_404(prontuario_id)
    paciente = Paciente.query.get_or_404(prontuario.paciente_id)

    return render_template('documentos/laudo.html',
                         prontuario=prontuario,
                         paciente=paciente,
                         medico=Config.MEDICO_NOME,
                         crm=Config.MEDICO_CRM)

@documentos_bp.route('/laudo/<int:prontuario_id>/salvar', methods=['POST'])
def salvar_laudo(prontuario_id):
    """Salva laudo no banco de dados"""
    try:
        prontuario = Prontuario.query.get_or_404(prontuario_id)

        laudo = Laudo(
            paciente_id=prontuario.paciente_id,
            prontuario_id=prontuario_id,
            tipo_exame=request.form.get('tipo_exame', '').strip(),
            titulo=request.form.get('titulo', '').strip(),
            conteudo=request.form.get('conteudo', '').strip(),
            conclusao=request.form.get('conclusao', '').strip()
        )

        db.session.add(laudo)
        db.session.commit()

        flash('Laudo salvo com sucesso!', 'success')
        return redirect(url_for('documentos.gerar_laudo', prontuario_id=prontuario_id))
    except Exception as e:
        flash(f'Erro ao salvar laudo: {str(e)}', 'error')
        return redirect(url_for('prontuario.ver_prontuario', paciente_id=prontuario.paciente_id))

@documentos_bp.route('/atestado/<int:prontuario_id>')
def gerar_atestado(prontuario_id):
    """Gera atestado médico"""
    prontuario = Prontuario.query.get_or_404(prontuario_id)
    paciente = Paciente.query.get_or_404(prontuario.paciente_id)

    # Buscar atestado salvo
    atestado_existente = Atestado.query.filter_by(prontuario_id=prontuario_id).first()

    return render_template('documentos/atestado.html',
                         prontuario=prontuario,
                         paciente=paciente,
                         atestado=atestado_existente,
                         medico=Config.MEDICO_NOME,
                         crm=Config.MEDICO_CRM,
                         config=Config)

@documentos_bp.route('/atestado/<int:prontuario_id>/salvar', methods=['POST'])
def salvar_atestado(prontuario_id):
    """Salva atestado no banco de dados"""
    try:
        prontuario = Prontuario.query.get_or_404(prontuario_id)

        dias = int(request.form.get('dias_afastamento', 0))
        data_inicio = datetime.strptime(request.form.get('data_inicio'), '%Y-%m-%d').date()
        data_fim = data_inicio + timedelta(days=dias) if dias > 0 else None

        atestado = Atestado(
            paciente_id=prontuario.paciente_id,
            prontuario_id=prontuario_id,
            cid=request.form.get('cid', '').strip(),
            dias_afastamento=dias,
            data_inicio=data_inicio,
            data_fim=data_fim,
            observacoes=request.form.get('observacoes', '').strip()
        )

        db.session.add(atestado)
        db.session.commit()

        flash('Atestado salvo com sucesso!', 'success')
        return redirect(url_for('documentos.gerar_atestado', prontuario_id=prontuario_id))
    except Exception as e:
        flash(f'Erro ao salvar atestado: {str(e)}', 'error')
        return redirect(url_for('prontuario.ver_prontuario', paciente_id=prontuario.paciente_id))

@documentos_bp.route('/recibo/<int:agendamento_id>')
def gerar_recibo(agendamento_id):
    """Gera recibo de pagamento"""
    agendamento = Agendamento.query.get_or_404(agendamento_id)
    paciente = Paciente.query.get_or_404(agendamento.paciente_id)

    # Verificar se já existe recibo
    recibo_existente = Recibo.query.filter_by(agendamento_id=agendamento_id).first()

    return render_template('documentos/recibo.html',
                         agendamento=agendamento,
                         paciente=paciente,
                         recibo=recibo_existente,
                         clinic_name=Config.CLINIC_NAME,
                         clinic_cnpj=Config.CLINIC_CNPJ)

@documentos_bp.route('/recibo/<int:agendamento_id>/salvar', methods=['POST'])
def salvar_recibo(agendamento_id):
    """Salva ou atualiza recibo"""
    try:
        agendamento = Agendamento.query.get_or_404(agendamento_id)

        # Verificar se já existe
        recibo = Recibo.query.filter_by(agendamento_id=agendamento_id).first()

        valor = float(request.form.get('valor', 0))
        forma_pagamento = request.form.get('forma_pagamento', '').strip()

        if recibo:
            # Atualizar existente
            recibo.valor = valor
            recibo.forma_pagamento = forma_pagamento
            recibo.descricao_servico = agendamento.servico
        else:
            # Criar novo
            numero_recibo = f"REC-{datetime.now().strftime('%Y%m%d')}-{agendamento_id}"

            recibo = Recibo(
                paciente_id=agendamento.paciente_id,
                agendamento_id=agendamento_id,
                descricao_servico=agendamento.servico,
                valor=valor,
                forma_pagamento=forma_pagamento,
                numero_recibo=numero_recibo
            )
            db.session.add(recibo)

        db.session.commit()
        flash('Recibo salvo com sucesso!', 'success')
        return redirect(url_for('documentos.gerar_recibo', agendamento_id=agendamento_id))
    except Exception as e:
        flash(f'Erro ao salvar recibo: {str(e)}', 'error')
        return redirect(url_for('documentos.gerar_recibo', agendamento_id=agendamento_id))

@documentos_bp.route('/pedido-exame/<int:prontuario_id>')
def gerar_pedido_exame(prontuario_id):
    """Gera pedido de exame"""
    prontuario = Prontuario.query.get_or_404(prontuario_id)
    paciente = Paciente.query.get_or_404(prontuario.paciente_id)

    # Listar exames disponíveis (exceto consulta)
    exames_disponiveis = [s for s in Config.SERVICOS_DISPONIVEIS if s != 'Consulta Médica']

    return render_template('documentos/pedido_exame.html',
                         prontuario=prontuario,
                         paciente=paciente,
                         exames=exames_disponiveis,
                         medico=Config.MEDICO_NOME,
                         crm=Config.MEDICO_CRM,
                         config=Config)

@documentos_bp.route('/pedido-exame/<int:prontuario_id>/salvar', methods=['POST'])
def salvar_pedido_exame(prontuario_id):
    """Salva pedido de exame no banco de dados"""
    try:
        prontuario = Prontuario.query.get_or_404(prontuario_id)

        # Pegar exames selecionados
        exames_selecionados = request.form.getlist('exames[]')
        indicacao_clinica = request.form.get('indicacao_clinica', '').strip()
        observacoes = request.form.get('observacoes', '').strip()

        # Atualizar campos do prontuário
        if exames_selecionados:
            prontuario.exames_solicitados = ', '.join(exames_selecionados)
        if indicacao_clinica:
            prontuario.indicacao_clinica = indicacao_clinica
        if observacoes and not prontuario.observacoes:
            prontuario.observacoes = observacoes

        db.session.commit()

        flash('Pedido de exame salvo com sucesso!', 'success')
        return redirect(url_for('documentos.gerar_pedido_exame', prontuario_id=prontuario_id))
    except Exception as e:
        flash(f'Erro ao salvar pedido: {str(e)}', 'error')
        return redirect(url_for('prontuario.ver_prontuario', paciente_id=prontuario.paciente_id))

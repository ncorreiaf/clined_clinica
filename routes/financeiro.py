"""
Rotas do Módulo 3 - Financeiro
Gerencia todas as funcionalidades relacionadas ao controle financeiro
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.models import db, ContaReceber, ContaPagar, FluxoCaixa, Paciente, Profissional, Agendamento
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_
from decimal import Decimal
from utils.auth_helpers import get_usuario_atual

# Criação do Blueprint para financeiro
financeiro_bp = Blueprint('financeiro', __name__)

# Context processor para disponibilizar 'date' em todos os templates do financeiro
@financeiro_bp.context_processor
def utility_processor():
    return dict(date=date, datetime=datetime)

@financeiro_bp.route('/dashboard')
def dashboard():
    """
    Dashboard financeiro com resumo geral
    """
    try:
        hoje = date.today()
        inicio_mes = hoje.replace(day=1)
        
        # Contas a receber
        total_receber = db.session.query(func.sum(ContaReceber.valor)).filter(
            ContaReceber.status == 'pendente'
        ).scalar() or 0
        
        vencidas_receber = db.session.query(func.sum(ContaReceber.valor)).filter(
            and_(ContaReceber.status == 'pendente', ContaReceber.data_vencimento < hoje)
        ).scalar() or 0
        
        # Contas a pagar
        total_pagar = db.session.query(func.sum(ContaPagar.valor)).filter(
            ContaPagar.status == 'pendente'
        ).scalar() or 0
        
        vencidas_pagar = db.session.query(func.sum(ContaPagar.valor)).filter(
            and_(ContaPagar.status == 'pendente', ContaPagar.data_vencimento < hoje)
        ).scalar() or 0
        
        # Fluxo de caixa do mês
        entradas_mes = db.session.query(func.sum(FluxoCaixa.valor)).filter(
            and_(FluxoCaixa.tipo == 'entrada', 
                 FluxoCaixa.data_movimento >= inicio_mes,
                 FluxoCaixa.data_movimento <= hoje)
        ).scalar() or 0
        
        saidas_mes = db.session.query(func.sum(FluxoCaixa.valor)).filter(
            and_(FluxoCaixa.tipo == 'saida', 
                 FluxoCaixa.data_movimento >= inicio_mes,
                 FluxoCaixa.data_movimento <= hoje)
        ).scalar() or 0
        
        saldo_mes = entradas_mes - saidas_mes
        
        return render_template('financeiro/dashboard.html',
                             total_receber=total_receber,
                             vencidas_receber=vencidas_receber,
                             total_pagar=total_pagar,
                             vencidas_pagar=vencidas_pagar,
                             entradas_mes=entradas_mes,
                             saidas_mes=saidas_mes,
                             saldo_mes=saldo_mes)
                             
    except Exception as e:
        flash(f'Erro ao carregar dashboard financeiro: {str(e)}', 'error')
        return render_template('financeiro/dashboard.html',
                             total_receber=0, vencidas_receber=0,
                             total_pagar=0, vencidas_pagar=0,
                             entradas_mes=0, saidas_mes=0, saldo_mes=0)

@financeiro_bp.route('/contas-receber')
def contas_receber():
    """
    Lista de contas a receber
    """
    status_filtro = request.args.get('status', 'todas')
    
    query = ContaReceber.query
    
    if status_filtro != 'todas':
        query = query.filter(ContaReceber.status == status_filtro)
    
    contas = query.order_by(ContaReceber.data_vencimento).all()
    
    return render_template('financeiro/contas_receber.html', 
                         contas=contas, 
                         status_filtro=status_filtro)

@financeiro_bp.route('/contas-receber/nova', methods=['GET', 'POST'])
def nova_conta_receber():
    """
    Criar nova conta a receber
    """
    if request.method == 'POST':
        try:
            paciente_id = request.form['paciente_id']
            agendamento_id = request.form.get('agendamento_id') or None
            descricao = request.form['descricao'].strip()
            valor = Decimal(request.form['valor'])
            data_vencimento = datetime.strptime(request.form['data_vencimento'], '%Y-%m-%d').date()
            observacoes = request.form.get('observacoes', '').strip()
            forma_pagamento = request.form.get('forma_pagamento', '').strip()

            # Criar a conta
            nova_conta = ContaReceber(
                paciente_id=paciente_id,
                agendamento_id=agendamento_id,
                descricao=descricao,
                valor=valor,
                data_vencimento=data_vencimento,
                observacoes=observacoes,
                forma_pagamento=forma_pagamento
            )

            # Se for cortesia, já marcar como concluída
            if forma_pagamento == 'Cortesia':
                nova_conta.status = 'pago'
                nova_conta.data_pagamento = date.today()

                # Registrar no fluxo de caixa como cortesia
                paciente = Paciente.query.get(paciente_id)
                movimento = FluxoCaixa(
                    data_movimento=date.today(),
                    tipo='entrada',
                    categoria='Cortesia',
                    descricao=f'Cortesia: {descricao}',
                    valor=valor,
                    recepcionista=paciente.nome if paciente else '',
                    forma_pagamento='Cortesia'
                )
                db.session.add(movimento)
                flash('Conta criada e registrada como cortesia (gratuito)!', 'success')
            else:
                # Conta normal fica como pendente
                flash('Conta a receber criada com sucesso! Clique em "Pagar" na lista quando receber.', 'success')

            db.session.add(nova_conta)
            db.session.commit()

            return redirect(url_for('financeiro.contas_receber'))

        except Exception as e:
            flash(f'Erro ao criar conta a receber: {str(e)}', 'error')
            db.session.rollback()

    pacientes = Paciente.query.order_by(Paciente.nome).all()
    agendamentos = Agendamento.query.filter(Agendamento.status == 'finalizado').all()

    return render_template('financeiro/nova_conta_receber.html',
                         pacientes=pacientes,
                         agendamentos=agendamentos)

@financeiro_bp.route('/contas-pagar')
def contas_pagar():
    """
    Lista de contas a pagar
    """
    status_filtro = request.args.get('status', 'todas')
    
    query = ContaPagar.query
    
    if status_filtro != 'todas':
        query = query.filter(ContaPagar.status == status_filtro)
    
    contas = query.order_by(ContaPagar.data_vencimento).all()
    
    return render_template('financeiro/contas_pagar.html', 
                         contas=contas, 
                         status_filtro=status_filtro)

@financeiro_bp.route('/contas-pagar/nova', methods=['GET', 'POST'])
def nova_conta_pagar():
    """
    Criar nova conta a pagar
    """
    if request.method == 'POST':
        try:
            fornecedor = request.form['fornecedor'].strip()
            descricao = request.form['descricao'].strip()
            valor = Decimal(request.form['valor'])
            data_vencimento = datetime.strptime(request.form['data_vencimento'], '%Y-%m-%d').date()
            categoria = request.form['categoria'].strip()
            centro_custo = request.form.get('centro_custo', '').strip()
            observacoes = request.form.get('observacoes', '').strip()
            forma_pagamento = request.form.get('forma_pagamento', '').strip()

            nova_conta = ContaPagar(
                fornecedor=fornecedor,
                descricao=descricao,
                valor=valor,
                data_vencimento=data_vencimento,
                categoria=categoria,
                forma_pagamento=forma_pagamento,
                centro_custo=centro_custo,
                observacoes=observacoes
            )
            
            db.session.add(nova_conta)
            db.session.commit()
            
            flash('Conta a pagar criada com sucesso!', 'success')
            return redirect(url_for('financeiro.contas_pagar'))
            
        except Exception as e:
            flash(f'Erro ao criar conta a pagar: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('financeiro/nova_conta_pagar.html')

@financeiro_bp.route('/fluxo-caixa')
def fluxo_caixa():
    """
    Relatório de fluxo de caixa
    """
    data_inicio = request.args.get('data_inicio', date.today().replace(day=1).strftime('%Y-%m-%d'))
    data_fim = request.args.get('data_fim', date.today().strftime('%Y-%m-%d'))

    movimentos = FluxoCaixa.query.filter(
        and_(FluxoCaixa.data_movimento >= data_inicio,
             FluxoCaixa.data_movimento <= data_fim)
    ).order_by(FluxoCaixa.data_movimento.desc()).all()

    # Preencher responsável dinamicamente se estiver vazio
    for movimento in movimentos:
        if not movimento.recepcionista or movimento.recepcionista == '':
            if movimento.conta_receber_id:
                conta_receber = ContaReceber.query.get(movimento.conta_receber_id)
                if conta_receber and conta_receber.paciente_conta:
                    movimento.recepcionista = conta_receber.paciente_conta.nome
            elif movimento.conta_pagar_id:
                conta_pagar = ContaPagar.query.get(movimento.conta_pagar_id)
                if conta_pagar:
                    movimento.recepcionista = conta_pagar.fornecedor

    # Calcular totais
    total_entradas = sum(m.valor for m in movimentos if m.tipo == 'entrada')
    total_saidas = sum(m.valor for m in movimentos if m.tipo == 'saida')
    saldo = total_entradas - total_saidas

    return render_template('financeiro/fluxo_caixa.html',
                         movimentos=movimentos,
                         data_inicio=data_inicio,
                         data_fim=data_fim,
                         total_entradas=total_entradas,
                         total_saidas=total_saidas,
                         saldo=saldo)


@financeiro_bp.route('/pagar-conta/<int:conta_id>', methods=['POST'])
def pagar_conta(conta_id):
    """
    Marcar conta como paga
    """
    try:
        conta = ContaPagar.query.get_or_404(conta_id)

        conta.status = 'pago'
        conta.data_pagamento = date.today()

        # Registrar no fluxo de caixa
        movimento = FluxoCaixa(
            data_movimento=date.today(),
            tipo='saida',
            categoria=conta.categoria,
            descricao=f'Pagamento: {conta.descricao}',
            valor=conta.valor,
            conta_pagar_id=conta.id,
            recepcionista=conta.fornecedor,
            forma_pagamento=conta.forma_pagamento
        )

        db.session.add(movimento)
        db.session.commit()

        flash(f'Conta marcada como paga via {conta.forma_pagamento}!', 'success')

    except Exception as e:
        flash(f'Erro ao pagar conta: {str(e)}', 'error')
        db.session.rollback()

    return redirect(url_for('financeiro.contas_pagar'))

@financeiro_bp.route('/receber-conta/<int:conta_id>', methods=['POST'])
def receber_conta(conta_id):
    """
    Marcar conta como recebida
    """
    try:
        conta = ContaReceber.query.get_or_404(conta_id)

        conta.status = 'pago'
        conta.data_pagamento = date.today()

        # Registrar no fluxo de caixa
        if conta.forma_pagamento == 'Cortesia':
            categoria = 'Cortesia'
        else:
            categoria = 'Receita de Serviços'

        movimento = FluxoCaixa(
            data_movimento=date.today(),
            tipo='entrada',
            categoria=categoria,
            descricao=f'Recebimento: {conta.descricao}',
            valor=conta.valor,
            conta_receber_id=conta.id,
            recepcionista=conta.paciente_conta.nome,
            forma_pagamento=conta.forma_pagamento
        )

        db.session.add(movimento)
        db.session.commit()

        flash(f'Pagamento recebido via {conta.forma_pagamento}!', 'success')

    except Exception as e:
        flash(f'Erro ao receber conta: {str(e)}', 'error')
        db.session.rollback()

    return redirect(url_for('financeiro.contas_receber'))


# Novas rotas para API/JSON
@financeiro_bp.route('/api/contas-receber')
def api_contas_receber():
    """
    API para obter contas a receber em formato JSON
    """
    contas = ContaReceber.query.order_by(ContaReceber.data_vencimento).all()
    
    contas_data = []
    for conta in contas:
        contas_data.append({
            'id': conta.id,
            'paciente_nome': conta.paciente_conta.nome,
            'descricao': conta.descricao,
            'valor': float(conta.valor),
            'data_vencimento': conta.data_vencimento.strftime('%Y-%m-%d'),
            'status': conta.status,
            'data_pagamento': conta.data_pagamento.strftime('%Y-%m-%d') if conta.data_pagamento else None
        })
    
    return jsonify(contas_data)

@financeiro_bp.route('/api/contas-pagar')
def api_contas_pagar():
    """
    API para obter contas a pagar em formato JSON
    """
    contas = ContaPagar.query.order_by(ContaPagar.data_vencimento).all()
    
    contas_data = []
    for conta in contas:
        contas_data.append({
            'id': conta.id,
            'fornecedor': conta.fornecedor,
            'descricao': conta.descricao,
            'valor': float(conta.valor),
            'data_vencimento': conta.data_vencimento.strftime('%Y-%m-%d'),
            'status': conta.status,
            'categoria': conta.categoria
        })
    
    return jsonify(contas_data)

@financeiro_bp.route('/api/fluxo-caixa/<string:periodo>')
def api_fluxo_caixa(periodo):
    """
    API para obter fluxo de caixa por período
    """
    hoje = date.today()
    
    if periodo == 'mes_atual':
        inicio = hoje.replace(day=1)
        fim = hoje
    elif periodo == 'mes_anterior':
        primeiro_dia_mes_atual = hoje.replace(day=1)
        fim = primeiro_dia_mes_atual - timedelta(days=1)
        inicio = fim.replace(day=1)
    else:  # ultimos_30_dias
        inicio = hoje - timedelta(days=30)
        fim = hoje
    
    movimentos = FluxoCaixa.query.filter(
        and_(FluxoCaixa.data_movimento >= inicio,
             FluxoCaixa.data_movimento <= fim)
    ).order_by(FluxoCaixa.data_movimento).all()
    
    fluxo_data = []
    for movimento in movimentos:
        fluxo_data.append({
            'data': movimento.data_movimento.strftime('%Y-%m-%d'),
            'tipo': movimento.tipo,
            'categoria': movimento.categoria,
            'descricao': movimento.descricao,
            'valor': float(movimento.valor)
        })
    
    return jsonify(fluxo_data)
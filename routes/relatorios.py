"""
Rotas do Módulo 4 - Relatórios e Indicadores
Gerencia dashboards, relatórios e indicadores de performance
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.models import (db, Agendamento, Paciente, Profissional, ContaReceber, ContaPagar, 
                          FluxoCaixa, AvaliacaoSatisfacao, LogAuditoria, AlertaAutomatico)
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_, extract
from decimal import Decimal
import json

# Criação do Blueprint para relatórios
relatorios_bp = Blueprint('relatorios', __name__)

@relatorios_bp.route('/dashboard')
def dashboard():
    """
    Dashboard gerencial principal
    """
    try:
        hoje = date.today()
        inicio_mes = hoje.replace(day=1)
        inicio_ano = hoje.replace(month=1, day=1)
        
        # Indicadores gerais
        total_pacientes = Paciente.query.count()
        total_profissionais = Profissional.query.filter_by(ativo=True).count()
        
        # Atendimentos
        atendimentos_mes = Agendamento.query.filter(
            and_(func.date(Agendamento.data_agendamento) >= inicio_mes,
                 func.date(Agendamento.data_agendamento) <= hoje,
                 Agendamento.status == 'finalizado')
        ).count()
        
        atendimentos_ano = Agendamento.query.filter(
            and_(func.date(Agendamento.data_agendamento) >= inicio_ano,
                 func.date(Agendamento.data_agendamento) <= hoje,
                 Agendamento.status == 'finalizado')
        ).count()
        
        # Faturamento
        faturamento_mes = db.session.query(func.sum(ContaReceber.valor)).filter(
            and_(ContaReceber.data_criacao >= inicio_mes,
                 ContaReceber.data_criacao <= hoje)
        ).scalar() or 0
        
        faturamento_ano = db.session.query(func.sum(ContaReceber.valor)).filter(
            and_(ContaReceber.data_criacao >= inicio_ano,
                 ContaReceber.data_criacao <= hoje)
        ).scalar() or 0
        
        # Ticket médio
        ticket_medio = faturamento_mes / atendimentos_mes if atendimentos_mes > 0 else 0
        
        # NPS médio
        nps_medio = db.session.query(func.avg(AvaliacaoSatisfacao.nota_nps)).filter(
            AvaliacaoSatisfacao.data_avaliacao >= inicio_mes
        ).scalar() or 0
        
        # Alertas ativos
        alertas_ativos = AlertaAutomatico.query.filter_by(status='ativo').count()
        
        return render_template('relatorios/dashboard.html',
                             total_pacientes=total_pacientes,
                             total_profissionais=total_profissionais,
                             atendimentos_mes=atendimentos_mes,
                             atendimentos_ano=atendimentos_ano,
                             faturamento_mes=faturamento_mes,
                             faturamento_ano=faturamento_ano,
                             ticket_medio=ticket_medio,
                             nps_medio=nps_medio,
                             alertas_ativos=alertas_ativos)
                             
    except Exception as e:
        flash(f'Erro ao carregar dashboard: {str(e)}', 'error')
        return render_template('relatorios/dashboard.html')

@relatorios_bp.route('/faturamento')
def faturamento():
    """
    Relatório de faturamento por empresa e profissional
    """
    data_inicio = request.args.get('data_inicio', date.today().replace(day=1).strftime('%Y-%m-%d'))
    data_fim = request.args.get('data_fim', date.today().strftime('%Y-%m-%d'))
    
    # Faturamento por profissional
    faturamento_profissional = db.session.query(
        Profissional.nome,
        Profissional.especialidade,
        func.count(Agendamento.id).label('total_atendimentos'),
        func.sum(ContaReceber.valor).label('faturamento_total')
    ).join(
        Agendamento, Profissional.id == Agendamento.profissional_id
    ).join(
        ContaReceber, Agendamento.id == ContaReceber.agendamento_id
    ).filter(
        and_(ContaReceber.data_criacao >= data_inicio,
             ContaReceber.data_criacao <= data_fim)
    ).group_by(Profissional.id).all()
    
    # Faturamento por especialidade
    faturamento_especialidade = db.session.query(
        Profissional.especialidade,
        func.count(Agendamento.id).label('total_atendimentos'),
        func.sum(ContaReceber.valor).label('faturamento_total')
    ).join(
        Agendamento, Profissional.id == Agendamento.profissional_id
    ).join(
        ContaReceber, Agendamento.id == ContaReceber.agendamento_id
    ).filter(
        and_(ContaReceber.data_criacao >= data_inicio,
             ContaReceber.data_criacao <= data_fim)
    ).group_by(Profissional.especialidade).all()
    
    return render_template('relatorios/faturamento.html',
                         faturamento_profissional=faturamento_profissional,
                         faturamento_especialidade=faturamento_especialidade,
                         data_inicio=data_inicio,
                         data_fim=data_fim)

@relatorios_bp.route('/ticket-medio')
def ticket_medio():
    """
    Relatório de ticket médio por profissional
    """
    data_inicio = request.args.get('data_inicio', date.today().replace(day=1).strftime('%Y-%m-%d'))
    data_fim = request.args.get('data_fim', date.today().strftime('%Y-%m-%d'))
    
    ticket_medio_profissional = db.session.query(
        Profissional.nome,
        Profissional.especialidade,
        func.count(Agendamento.id).label('total_atendimentos'),
        func.sum(ContaReceber.valor).label('faturamento_total'),
        (func.sum(ContaReceber.valor) / func.count(Agendamento.id)).label('ticket_medio')
    ).join(
        Agendamento, Profissional.id == Agendamento.profissional_id
    ).join(
        ContaReceber, Agendamento.id == ContaReceber.agendamento_id
    ).filter(
        and_(ContaReceber.data_criacao >= data_inicio,
             ContaReceber.data_criacao <= data_fim)
    ).group_by(Profissional.id).all()
    
    return render_template('relatorios/ticket_medio.html',
                         ticket_medio_profissional=ticket_medio_profissional,
                         data_inicio=data_inicio,
                         data_fim=data_fim)

@relatorios_bp.route('/nps')
def nps():
    """
    Relatório de NPS (Net Promoter Score)
    """
    data_inicio = request.args.get('data_inicio', date.today().replace(day=1).strftime('%Y-%m-%d'))
    data_fim = request.args.get('data_fim', date.today().strftime('%Y-%m-%d'))
    
    # Avalições no período
    avaliacoes = AvaliacaoSatisfacao.query.filter(
        and_(func.date(AvaliacaoSatisfacao.data_avaliacao) >= data_inicio,
             func.date(AvaliacaoSatisfacao.data_avaliacao) <= data_fim)
    ).all()
    
    # Calcular NPS
    total_avaliacoes = len(avaliacoes)
    if total_avaliacoes > 0:
        promotores = len([a for a in avaliacoes if a.nota_nps >= 9])
        neutros = len([a for a in avaliacoes if 7 <= a.nota_nps <= 8])
        detratores = len([a for a in avaliacoes if a.nota_nps <= 6])
        
        nps_score = ((promotores - detratores) / total_avaliacoes) * 100
    else:
        promotores = neutros = detratores = nps_score = 0
    
    # NPS por profissional
    nps_profissional = db.session.query(
        Profissional.nome,
        func.count(AvaliacaoSatisfacao.id).label('total_avaliacoes'),
        func.avg(AvaliacaoSatisfacao.nota_nps).label('nota_media')
    ).join(
        AvaliacaoSatisfacao, Profissional.id == AvaliacaoSatisfacao.profissional_id
    ).filter(
        and_(func.date(AvaliacaoSatisfacao.data_avaliacao) >= data_inicio,
             func.date(AvaliacaoSatisfacao.data_avaliacao) <= data_fim)
    ).group_by(Profissional.id).all()
    
    return render_template('relatorios/nps.html',
                         avaliacoes=avaliacoes,
                         total_avaliacoes=total_avaliacoes,
                         promotores=promotores,
                         neutros=neutros,
                         detratores=detratores,
                         nps_score=nps_score,
                         nps_profissional=nps_profissional,
                         data_inicio=data_inicio,
                         data_fim=data_fim)
@relatorios_bp.route('/alertas')
def alertas():
    """
    Gestão de alertas automáticos
    """
    status_filtro = request.args.get('status', 'ativo')
    
    query = AlertaAutomatico.query
    if status_filtro != 'todos':
        query = query.filter(AlertaAutomatico.status == status_filtro)
    
    alertas = query.order_by(AlertaAutomatico.data_criacao.desc()).all()
    
    return render_template('relatorios/alertas.html',
                         alertas=alertas,
                         status_filtro=status_filtro)

@relatorios_bp.route('/avaliar-satisfacao/<int:agendamento_id>', methods=['GET', 'POST'])
def avaliar_satisfacao(agendamento_id):
    """
    Formulário de avaliação de satisfação
    """
    agendamento = Agendamento.query.get_or_404(agendamento_id)
    
    if request.method == 'POST':
        try:
            nota_nps = int(request.form['nota_nps'])
            comentario = request.form.get('comentario', '')
            
            avaliacao = AvaliacaoSatisfacao(
                paciente_id=agendamento.paciente_id,
                agendamento_id=agendamento_id,
                profissional_id=agendamento.profissional_id,
                nota_nps=nota_nps,
                comentario=comentario
            )
            
            db.session.add(avaliacao)
            db.session.commit()
            
            flash('Avaliação registrada com sucesso!', 'success')
            return redirect(url_for('relatorios.nps'))
            
        except Exception as e:
            flash(f'Erro ao registrar avaliação: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('relatorios/avaliar_satisfacao.html', agendamento=agendamento)

@relatorios_bp.route('/avaliacao-publica/<int:agendamento_id>', methods=['GET', 'POST'])
def avaliacao_publica(agendamento_id):
    """
    Formulário de avaliação de satisfação público (sem autenticação)
    Para enviar ao cliente via WhatsApp/Email
    """
    agendamento = Agendamento.query.get_or_404(agendamento_id)

    # Verificar se já existe avaliação para este agendamento
    avaliacao_existente = AvaliacaoSatisfacao.query.filter_by(agendamento_id=agendamento_id).first()

    if request.method == 'POST':
        try:
            nota_nps = int(request.form['nota_nps'])
            comentario = request.form.get('comentario', '')

            if avaliacao_existente:
                # Atualizar avaliação existente
                avaliacao_existente.nota_nps = nota_nps
                avaliacao_existente.comentario = comentario
                avaliacao_existente.data_avaliacao = datetime.now()
                mensagem = 'Avaliação atualizada com sucesso!'
            else:
                # Criar nova avaliação
                nova_avaliacao = AvaliacaoSatisfacao(
                    paciente_id=agendamento.paciente_id,
                    agendamento_id=agendamento_id,
                    profissional_id=agendamento.profissional_id,
                    nota_nps=nota_nps,
                    comentario=comentario
                )
                db.session.add(nova_avaliacao)
                mensagem = 'Avaliação registrada com sucesso!'

            db.session.commit()

            return render_template('relatorios/avaliacao_sucesso.html',
                                 mensagem=mensagem,
                                 nota=nota_nps)

        except Exception as e:
            db.session.rollback()
            return render_template('relatorios/avaliacao_erro.html',
                                 erro=str(e))

    return render_template('relatorios/avaliacao_publica.html',
                         agendamento=agendamento,
                         avaliacao_existente=avaliacao_existente)

@relatorios_bp.route('/gerar-alertas')
def gerar_alertas():
    """
    Verifica e gera alertas automáticos do sistema
    """
    try:
        hoje = date.today()
        alertas_criados = 0

        # 1. Alertas de contas vencidas
        contas_vencidas_receber = ContaReceber.query.filter(
            and_(ContaReceber.status == 'pendente',
                 ContaReceber.data_vencimento < hoje)
        ).all()

        for conta in contas_vencidas_receber:
            # Verificar se já existe alerta ativo para esta conta
            alerta_existente = AlertaAutomatico.query.filter(
                and_(AlertaAutomatico.tipo == 'vencimento',
                     AlertaAutomatico.descricao.contains(f'Conta a receber #{conta.id}'),
                     AlertaAutomatico.status == 'ativo')
            ).first()

            if not alerta_existente:
                dias_vencido = (hoje - conta.data_vencimento).days
                alerta = AlertaAutomatico(
                    tipo='vencimento',
                    titulo=f'Conta a Receber Vencida',
                    descricao=f'Conta a receber #{conta.id} de {conta.paciente_conta.nome} - R$ {conta.valor:.2f} - Vencida há {dias_vencido} dias',
                    prioridade='alta' if dias_vencido > 30 else 'media'
                )
                db.session.add(alerta)
                alertas_criados += 1

        contas_vencidas_pagar = ContaPagar.query.filter(
            and_(ContaPagar.status == 'pendente',
                 ContaPagar.data_vencimento < hoje)
        ).all()

        for conta in contas_vencidas_pagar:
            alerta_existente = AlertaAutomatico.query.filter(
                and_(AlertaAutomatico.tipo == 'vencimento',
                     AlertaAutomatico.descricao.contains(f'Conta a pagar #{conta.id}'),
                     AlertaAutomatico.status == 'ativo')
            ).first()

            if not alerta_existente:
                dias_vencido = (hoje - conta.data_vencimento).days
                alerta = AlertaAutomatico(
                    tipo='vencimento',
                    titulo=f'Conta a Pagar Vencida',
                    descricao=f'Conta a pagar #{conta.id} - {conta.fornecedor} - R$ {conta.valor:.2f} - Vencida há {dias_vencido} dias',
                    prioridade='alta' if dias_vencido > 15 else 'media'
                )
                db.session.add(alerta)
                alertas_criados += 1

        # 2. Alertas de metas não atingidas (verificar apenas no último dia do mês)
        import calendar
        ultimo_dia_mes = calendar.monthrange(hoje.year, hoje.month)[1]

        if hoje.day == ultimo_dia_mes:
            from models.models import MetaEmpresa
            meta_mes = MetaEmpresa.query.filter_by(mes=hoje.month, ano=hoje.year).first()

            if meta_mes:
                # Verificar faturamento
                inicio_mes = hoje.replace(day=1)
                faturamento_mes = db.session.query(func.sum(ContaReceber.valor)).filter(
                    and_(ContaReceber.data_criacao >= inicio_mes,
                         ContaReceber.data_criacao <= hoje)
                ).scalar() or 0

                if meta_mes.meta_faturamento > 0:
                    perc_fat = (float(faturamento_mes) / float(meta_mes.meta_faturamento)) * 100
                    if perc_fat < 80:
                        alerta_existente = AlertaAutomatico.query.filter(
                            and_(AlertaAutomatico.tipo == 'meta',
                                 AlertaAutomatico.descricao.contains(f'Faturamento {hoje.month}/{hoje.year}'),
                                 AlertaAutomatico.status == 'ativo')
                        ).first()

                        if not alerta_existente:
                            alerta = AlertaAutomatico(
                                tipo='meta',
                                titulo='Meta de Faturamento Não Atingida',
                                descricao=f'Faturamento {hoje.month}/{hoje.year}: {perc_fat:.1f}% da meta (R$ {faturamento_mes:.2f} de R$ {meta_mes.meta_faturamento:.2f})',
                                prioridade='alta' if perc_fat < 50 else 'media'
                            )
                            db.session.add(alerta)
                            alertas_criados += 1

        db.session.commit()
        flash(f'{alertas_criados} alerta(s) gerado(s) com sucesso!', 'success')

    except Exception as e:
        flash(f'Erro ao gerar alertas: {str(e)}', 'error')
        db.session.rollback()

    return redirect(url_for('relatorios.alertas'))

@relatorios_bp.route('/api/dados-dashboard')
def api_dados_dashboard():
    """
    API para dados do dashboard (gráficos)
    """
    try:
        hoje = date.today()
        inicio_mes = hoje.replace(day=1)
        
        # Atendimentos por dia (últimos 30 dias)
        atendimentos_diarios = []
        for i in range(30):
            data = hoje - timedelta(days=i)
            count = Agendamento.query.filter(
                and_(func.date(Agendamento.data_agendamento) == data,
                     Agendamento.status == 'finalizado')
            ).count()
            atendimentos_diarios.append({
                'data': data.strftime('%d/%m'),
                'atendimentos': count
            })
        
        # Faturamento por especialidade
        faturamento_especialidade = db.session.query(
            Profissional.especialidade,
            func.sum(ContaReceber.valor).label('total')
        ).join(
            Agendamento, Profissional.id == Agendamento.profissional_id
        ).join(
            ContaReceber, Agendamento.id == ContaReceber.agendamento_id
        ).filter(
            ContaReceber.data_criacao >= inicio_mes
        ).group_by(Profissional.especialidade).all()
        
        return jsonify({
            'atendimentos_diarios': list(reversed(atendimentos_diarios)),
            'faturamento_especialidade': [
                {'especialidade': item[0], 'valor': float(item[1] or 0)}
                for item in faturamento_especialidade
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@relatorios_bp.route('/resolver-alerta/<int:alerta_id>')
def resolver_alerta(alerta_id):
    """
    Marcar alerta como resolvido
    """
    try:
        alerta = AlertaAutomatico.query.get_or_404(alerta_id)
        alerta.status = 'resolvido'
        alerta.data_resolucao = datetime.utcnow()

        db.session.commit()
        flash('Alerta marcado como resolvido!', 'success')

    except Exception as e:
        flash(f'Erro ao resolver alerta: {str(e)}', 'error')
        db.session.rollback()

    return redirect(url_for('relatorios.alertas'))

@relatorios_bp.route('/feedback', methods=['GET', 'POST'])
def feedback_universal():
    """
    Página pública universal de avaliação NPS
    Link pode ser compartilhado livremente sem necessidade de agendamento específico
    """
    if request.method == 'POST':
        try:
            nota_nps = int(request.form['nota_nps'])
            comentario = request.form.get('comentario', '')
            nome_paciente = request.form.get('nome_paciente', 'Anônimo').strip()

            if not nome_paciente:
                nome_paciente = 'Anônimo'

            paciente = Paciente.query.filter_by(nome=nome_paciente).first()

            if not paciente:
                paciente = Paciente(
                    nome=nome_paciente,
                    cpf='000.000.000-00',
                    telefone='',
                    email=''
                )
                db.session.add(paciente)
                db.session.flush()

            profissional = Profissional.query.filter_by(ativo=True).first()

            nova_avaliacao = AvaliacaoSatisfacao(
                paciente_id=paciente.id,
                agendamento_id=None,
                profissional_id=profissional.id if profissional else None,
                nota_nps=nota_nps,
                comentario=comentario
            )

            db.session.add(nova_avaliacao)
            db.session.commit()

            return render_template('relatorios/avaliacao_sucesso.html',
                                 mensagem='Avaliação registrada com sucesso!',
                                 nota=nota_nps)

        except Exception as e:
            db.session.rollback()
            return render_template('relatorios/avaliacao_erro.html',
                                 erro=str(e))

    return render_template('relatorios/feedback_universal.html')
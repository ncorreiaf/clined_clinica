"""
Rotas do Módulo de Metas
Gerencia configuração de metas e dashboard de acompanhamento
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.models import db, MetaEmpresa, Agendamento, ContaReceber, Paciente
from datetime import datetime, date
from sqlalchemy import func, and_, extract
from decimal import Decimal

# Criação do Blueprint para metas
metas_bp = Blueprint('metas', __name__)

@metas_bp.route('/configurar', methods=['GET', 'POST'])
def configurar_metas():
    """
    Configuração de metas mensais
    """
    if request.method == 'POST':
        try:
            mes = int(request.form['mes'])
            ano = int(request.form['ano'])
            meta_faturamento = Decimal(request.form.get('meta_faturamento', 0))
            meta_atendimentos = int(request.form.get('meta_atendimentos', 0))
            meta_novos_clientes = int(request.form.get('meta_novos_clientes', 0))

            # Verificar se já existe meta para este mês/ano
            meta_existente = MetaEmpresa.query.filter_by(mes=mes, ano=ano).first()

            if meta_existente:
                # Atualizar meta existente
                meta_existente.meta_faturamento = meta_faturamento
                meta_existente.meta_atendimentos = meta_atendimentos
                meta_existente.meta_novos_clientes = meta_novos_clientes
                meta_existente.data_atualizacao = datetime.now()
                mensagem = 'Meta atualizada com sucesso!'
            else:
                # Criar nova meta
                nova_meta = MetaEmpresa(
                    mes=mes,
                    ano=ano,
                    meta_faturamento=meta_faturamento,
                    meta_atendimentos=meta_atendimentos,
                    meta_novos_clientes=meta_novos_clientes
                )
                db.session.add(nova_meta)
                mensagem = 'Meta criada com sucesso!'

            db.session.commit()
            flash(mensagem, 'success')
            return redirect(url_for('metas.dashboard_metas'))

        except Exception as e:
            flash(f'Erro ao salvar meta: {str(e)}', 'error')
            db.session.rollback()

    # Buscar metas existentes para os próximos 12 meses
    hoje = date.today()
    metas_existentes = MetaEmpresa.query.filter(
        and_(
            MetaEmpresa.ano >= hoje.year,
            db.or_(
                MetaEmpresa.ano > hoje.year,
                MetaEmpresa.mes >= hoje.month
            )
        )
    ).order_by(MetaEmpresa.ano, MetaEmpresa.mes).all()

    return render_template('metas/configurar.html',
                         metas_existentes=metas_existentes,
                         hoje=hoje)

@metas_bp.route('/dashboard')
def dashboard_metas():
    """
    Dashboard de acompanhamento de metas
    """
    try:
        # Filtros
        mes_filtro = request.args.get('mes', date.today().month, type=int)
        ano_filtro = request.args.get('ano', date.today().year, type=int)

        # Buscar meta do período
        meta = MetaEmpresa.query.filter_by(mes=mes_filtro, ano=ano_filtro).first()

        # Calcular realizado no período
        inicio_periodo = date(ano_filtro, mes_filtro, 1)
        if mes_filtro == 12:
            fim_periodo = date(ano_filtro, 12, 31)
        else:
            # Último dia do mês
            import calendar
            ultimo_dia = calendar.monthrange(ano_filtro, mes_filtro)[1]
            fim_periodo = date(ano_filtro, mes_filtro, ultimo_dia)

        # Faturamento realizado
        faturamento_realizado = db.session.query(func.sum(ContaReceber.valor)).filter(
            and_(
                ContaReceber.data_criacao >= inicio_periodo,
                ContaReceber.data_criacao <= fim_periodo
            )
        ).scalar() or 0

        # Atendimentos realizados
        atendimentos_realizados = Agendamento.query.filter(
            and_(
                func.date(Agendamento.data_agendamento) >= inicio_periodo,
                func.date(Agendamento.data_agendamento) <= fim_periodo,
                Agendamento.status == 'finalizado'
            )
        ).count()

        # Novos clientes no período
        novos_clientes = Paciente.query.filter(
            and_(
                func.date(Paciente.data_cadastro) >= inicio_periodo,
                func.date(Paciente.data_cadastro) <= fim_periodo
            )
        ).count()

        # Calcular percentuais de atingimento
        perc_faturamento = 0
        perc_atendimentos = 0
        perc_novos_clientes = 0

        if meta:
            if meta.meta_faturamento > 0:
                perc_faturamento = (float(faturamento_realizado) / float(meta.meta_faturamento)) * 100
            if meta.meta_atendimentos > 0:
                perc_atendimentos = (atendimentos_realizados / meta.meta_atendimentos) * 100
            if meta.meta_novos_clientes > 0:
                perc_novos_clientes = (novos_clientes / meta.meta_novos_clientes) * 100

        # Buscar histórico dos últimos 6 meses
        historico = []
        for i in range(6):
            # Calcular mês/ano
            mes_hist = mes_filtro - i
            ano_hist = ano_filtro

            if mes_hist <= 0:
                mes_hist += 12
                ano_hist -= 1

            # Buscar meta e realizados
            meta_hist = MetaEmpresa.query.filter_by(mes=mes_hist, ano=ano_hist).first()

            inicio_hist = date(ano_hist, mes_hist, 1)
            if mes_hist == 12:
                fim_hist = date(ano_hist, 12, 31)
            else:
                import calendar
                ultimo_dia_hist = calendar.monthrange(ano_hist, mes_hist)[1]
                fim_hist = date(ano_hist, mes_hist, ultimo_dia_hist)

            fat_hist = db.session.query(func.sum(ContaReceber.valor)).filter(
                and_(
                    ContaReceber.data_criacao >= inicio_hist,
                    ContaReceber.data_criacao <= fim_hist
                )
            ).scalar() or 0

            atend_hist = Agendamento.query.filter(
                and_(
                    func.date(Agendamento.data_agendamento) >= inicio_hist,
                    func.date(Agendamento.data_agendamento) <= fim_hist,
                    Agendamento.status == 'finalizado'
                )
            ).count()

            historico.append({
                'mes': mes_hist,
                'ano': ano_hist,
                'mes_nome': ['', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                           'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'][mes_hist],
                'meta_faturamento': float(meta_hist.meta_faturamento) if meta_hist else 0,
                'faturamento_realizado': float(fat_hist),
                'meta_atendimentos': meta_hist.meta_atendimentos if meta_hist else 0,
                'atendimentos_realizados': atend_hist
            })

        historico.reverse()

        return render_template('metas/dashboard.html',
                             meta=meta,
                             mes_filtro=mes_filtro,
                             ano_filtro=ano_filtro,
                             faturamento_realizado=faturamento_realizado,
                             atendimentos_realizados=atendimentos_realizados,
                             novos_clientes=novos_clientes,
                             perc_faturamento=perc_faturamento,
                             perc_atendimentos=perc_atendimentos,
                             perc_novos_clientes=perc_novos_clientes,
                             historico=historico)

    except Exception as e:
        flash(f'Erro ao carregar dashboard de metas: {str(e)}', 'error')
        return render_template('metas/dashboard.html',
                             meta=None,
                             mes_filtro=date.today().month,
                             ano_filtro=date.today().year,
                             faturamento_realizado=0,
                             atendimentos_realizados=0,
                             novos_clientes=0,
                             perc_faturamento=0,
                             perc_atendimentos=0,
                             perc_novos_clientes=0,
                             historico=[])

@metas_bp.route('/api/historico-metas')
def api_historico_metas():
    """
    API para obter histórico de metas em formato JSON
    """
    try:
        meses = int(request.args.get('meses', 6))
        hoje = date.today()

        historico = []
        for i in range(meses):
            mes = hoje.month - i
            ano = hoje.year

            if mes <= 0:
                mes += 12
                ano -= 1

            meta = MetaEmpresa.query.filter_by(mes=mes, ano=ano).first()

            historico.append({
                'mes': mes,
                'ano': ano,
                'mes_ano': f"{mes}/{ano}",
                'meta_faturamento': float(meta.meta_faturamento) if meta else 0,
                'meta_atendimentos': meta.meta_atendimentos if meta else 0,
                'meta_novos_clientes': meta.meta_novos_clientes if meta else 0
            })

        historico.reverse()
        return jsonify({'historico': historico})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@metas_bp.route('/excluir/<int:meta_id>')
def excluir_meta(meta_id):
    """
    Excluir uma meta
    """
    try:
        meta = MetaEmpresa.query.get_or_404(meta_id)
        db.session.delete(meta)
        db.session.commit()

        flash('Meta excluída com sucesso!', 'success')

    except Exception as e:
        flash(f'Erro ao excluir meta: {str(e)}', 'error')
        db.session.rollback()

    return redirect(url_for('metas.configurar_metas'))

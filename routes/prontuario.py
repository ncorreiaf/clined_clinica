"""
Rotas do Módulo 2 - Prontuário Eletrônico
Gerencia todas as funcionalidades relacionadas aos prontuários
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.models import db, Prontuario, Paciente, AtendimentoHistorico
from datetime import datetime
from utils.auth_helpers import medico_required, agendamento_required, get_usuario_atual

# Criação do Blueprint para prontuários
prontuario_bp = Blueprint('prontuario', __name__)

@prontuario_bp.route('/pacientes')
@agendamento_required
def lista_pacientes():
    """
    Rota para exibir lista de pacientes
    Permite busca por nome ou CPF
    """
    busca = request.args.get('busca', '')
    
    if busca:
        # Busca por nome ou CPF
        pacientes = Paciente.query.filter(
            (Paciente.nome.contains(busca)) | 
            (Paciente.cpf.contains(busca))
        ).all()
    else:
        # Lista todos os pacientes
        pacientes = Paciente.query.order_by(Paciente.nome).all()
    
    return render_template('prontuario/lista_pacientes.html', 
                         pacientes=pacientes, 
                         busca=busca)

@prontuario_bp.route('/ver/<int:paciente_id>')
@agendamento_required
def ver_prontuario(paciente_id):
    """
    Rota para visualizar prontuário completo do paciente
    Mostra histórico de atendimentos e informações gerais
    Recepcionistas podem visualizar, mas não editar
    """
    paciente = Paciente.query.get_or_404(paciente_id)
    usuario = get_usuario_atual()

    # Busca todos os prontuários do paciente
    prontuarios = Prontuario.query.filter_by(paciente_id=paciente_id)\
                                  .order_by(Prontuario.data_atendimento.desc()).all()

    return render_template('prontuario/ver_prontuario.html',
                         paciente=paciente,
                         prontuarios=prontuarios,
                         usuario=usuario)

@prontuario_bp.route('/editar/<int:paciente_id>', methods=['GET', 'POST'])
@medico_required
def editar_prontuario(paciente_id):
    """
    Rota para criar/editar entrada no prontuário
    Permite adicionar novos atendimentos ao histórico
    """
    paciente = Paciente.query.get_or_404(paciente_id)
    
    if request.method == 'POST':
        try:
            # Coleta dados do formulário com TRIM
            especialidade = request.form['especialidade'].strip()
            queixa_principal = request.form['queixa_principal'].strip()
            historia_doenca = request.form['historia_doenca'].strip()
            exame_fisico = request.form['exame_fisico'].strip()
            diagnostico = request.form['diagnostico'].strip()
            prescricao = request.form['prescricao'].strip()
            observacoes = request.form['observacoes'].strip()
            profissional_nome = request.form['profissional_nome'].strip()
            
            # Cria nova entrada no prontuário
            novo_prontuario = Prontuario(
                paciente_id=paciente_id,
                especialidade=especialidade,
                queixa_principal=queixa_principal,
                historia_doenca=historia_doenca,
                exame_fisico=exame_fisico,
                diagnostico=diagnostico,
                prescricao=prescricao,
                observacoes=observacoes,
                profissional_nome=profissional_nome
            )
            
            db.session.add(novo_prontuario)
            db.session.flush()  # Para obter o ID do prontuário
            
            # Adiciona entrada no histórico de atendimentos
            historico = AtendimentoHistorico(
                prontuario_id=novo_prontuario.id,
                tipo_atendimento='consulta',
                descricao=f"Consulta - {especialidade}: {queixa_principal}",
                profissional=profissional_nome
            )
            
            db.session.add(historico)
            db.session.commit()
            
            flash('Prontuário atualizado com sucesso!', 'success')
            return redirect(url_for('prontuario.ver_prontuario', paciente_id=paciente_id))
            
        except Exception as e:
            flash(f'Erro ao salvar prontuário: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('prontuario/editar_prontuario.html', paciente=paciente)

@prontuario_bp.route('/gerar-prescricao/<int:prontuario_id>')
@medico_required
def gerar_prescricao(prontuario_id):
    """
    Rota para gerar prescrição médica
    Utiliza template HTML para formatação do documento
    """
    prontuario = Prontuario.query.get_or_404(prontuario_id)
    paciente = prontuario.paciente_ref
    
    return render_template('documentos/prescricao.html', 
                         prontuario=prontuario, 
                         paciente=paciente)

@prontuario_bp.route('/gerar-pedido-exame/<int:prontuario_id>')
@medico_required
def gerar_pedido_exame(prontuario_id):
    """
    Rota para gerar pedido de exames
    """
    prontuario = Prontuario.query.get_or_404(prontuario_id)
    paciente = prontuario.paciente_ref
    
    return render_template('documentos/exames.html', 
                         prontuario=prontuario, 
                         paciente=paciente)

@prontuario_bp.route('/gerar-atestado/<int:prontuario_id>')
@medico_required
def gerar_atestado(prontuario_id):
    """
    Rota para gerar atestado médico
    """
    prontuario = Prontuario.query.get_or_404(prontuario_id)
    paciente = prontuario.paciente_ref
    
    return render_template('documentos/atestado.html', 
                         prontuario=prontuario, 
                         paciente=paciente)

@prontuario_bp.route('/gerar-recibo/<int:prontuario_id>')
@medico_required
def gerar_recibo(prontuario_id):
    """
    Rota para gerar recibo de atendimento
    """
    prontuario = Prontuario.query.get_or_404(prontuario_id)
    paciente = prontuario.paciente_ref

    return render_template('documentos/recibo.html',
                         prontuario=prontuario,
                         paciente=paciente)

@prontuario_bp.route('/editar-paciente/<int:paciente_id>', methods=['POST'])
@agendamento_required
def editar_paciente(paciente_id):
    """
    Rota para editar informações do paciente
    Atualiza os dados cadastrais do paciente
    """
    paciente = Paciente.query.get_or_404(paciente_id)

    try:
        # Atualizar dados do paciente
        paciente.nome = request.form['nome'].strip()
        paciente.cpf = request.form['cpf'].strip()
        paciente.telefone = request.form['telefone'].strip()
        paciente.email = request.form.get('email', '').strip()

        # Data de nascimento
        data_nascimento_str = request.form.get('data_nascimento', '').strip()
        if data_nascimento_str:
            paciente.data_nascimento = datetime.strptime(data_nascimento_str, '%Y-%m-%d').date()
            # Calcular idade
            hoje = datetime.now().date()
            idade = hoje.year - paciente.data_nascimento.year
            if (hoje.month, hoje.day) < (paciente.data_nascimento.month, paciente.data_nascimento.day):
                idade -= 1
            paciente.idade = idade

        paciente.naturalidade = request.form.get('naturalidade', '').strip()
        paciente.estado_civil = request.form.get('estado_civil', '').strip()
        paciente.religiao = request.form.get('religiao', '').strip()
        paciente.profissao = request.form.get('profissao', '').strip()
        paciente.filiacao_mae = request.form.get('filiacao_mae', '').strip()
        paciente.filiacao_pai = request.form.get('filiacao_pai', '').strip()
        paciente.endereco = request.form.get('endereco', '').strip()
        paciente.bairro = request.form.get('bairro', '').strip()
        paciente.cidade = request.form.get('cidade', '').strip()

        db.session.commit()
        flash('Dados do paciente atualizados com sucesso!', 'success')

    except Exception as e:
        flash(f'Erro ao atualizar paciente: {str(e)}', 'error')
        db.session.rollback()

    return redirect(url_for('prontuario.lista_pacientes'))

@prontuario_bp.route('/api/prontuarios-anteriores/<int:paciente_id>')
def api_prontuarios_anteriores(paciente_id):
    """
    API para retornar prontuários anteriores do paciente
    Usado para copiar conteúdo em documentos
    """
    try:
        from flask import jsonify

        prontuarios = Prontuario.query.filter_by(paciente_id=paciente_id)\
                                      .order_by(Prontuario.data_atendimento.desc())\
                                      .all()

        resultado = []
        for p in prontuarios:
            resultado.append({
                'id': p.id,
                'data_atendimento': p.data_atendimento.strftime('%d/%m/%Y'),
                'especialidade': p.especialidade or '',
                'queixa_principal': p.queixa_principal or '',
                'historia_doenca': p.historia_doenca or '',
                'exame_fisico': p.exame_fisico or '',
                'diagnostico': p.diagnostico or '',
                'prescricao': p.prescricao or '',
                'observacoes': p.observacoes or ''
            })

        return jsonify({'prontuarios': resultado})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

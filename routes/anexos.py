"""
Rotas para Anexos de Prontuários
Gerencia upload, listagem e download de arquivos
"""

from flask import Blueprint, request, redirect, url_for, flash, send_file, jsonify
from werkzeug.utils import secure_filename
from models.models import db, Paciente, AnexoProntuario
import os
from datetime import datetime

anexos_bp = Blueprint('anexos', __name__)

UPLOAD_FOLDER = 'uploads/anexos'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'txt', 'zip'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    """Verifica se a extensão do arquivo é permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size_str(size_bytes):
    """Converte bytes para string legível"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

@anexos_bp.route('/paciente/<int:paciente_id>/listar')
def listar_anexos(paciente_id):
    """Lista todos os anexos de um paciente"""
    anexos = AnexoProntuario.query.filter_by(paciente_id=paciente_id).order_by(AnexoProntuario.data_upload.desc()).all()

    anexos_data = []
    for anexo in anexos:
        anexos_data.append({
            'id': anexo.id,
            'nome_original': anexo.nome_original,
            'tipo_arquivo': anexo.tipo_arquivo,
            'tamanho': get_file_size_str(anexo.tamanho) if anexo.tamanho else 'N/A',
            'descricao': anexo.descricao or '',
            'data_upload': anexo.data_upload.strftime('%d/%m/%Y %H:%M'),
            'usuario_upload': anexo.usuario_upload or 'Sistema'
        })

    return jsonify({'anexos': anexos_data})

@anexos_bp.route('/paciente/<int:paciente_id>/upload', methods=['POST'])
def upload_anexo(paciente_id):
    """Faz upload de um arquivo anexo"""
    try:
        # Verificar se o paciente existe
        paciente = Paciente.query.get_or_404(paciente_id)

        # Verificar se há arquivo
        if 'arquivo' not in request.files:
            return jsonify({'success': False, 'error': 'Nenhum arquivo selecionado'}), 400

        arquivo = request.files['arquivo']

        if arquivo.filename == '':
            return jsonify({'success': False, 'error': 'Nenhum arquivo selecionado'}), 400

        # Verificar extensão
        if not allowed_file(arquivo.filename):
            return jsonify({'success': False, 'error': 'Tipo de arquivo não permitido'}), 400

        # Verificar tamanho
        arquivo.seek(0, os.SEEK_END)
        file_size = arquivo.tell()
        arquivo.seek(0)

        if file_size > MAX_FILE_SIZE:
            return jsonify({'success': False, 'error': 'Arquivo muito grande (máximo 16MB)'}), 400

        # Criar diretório se não existir
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        # Gerar nome único
        nome_original = secure_filename(arquivo.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_arquivo = f"{paciente_id}_{timestamp}_{nome_original}"
        caminho_completo = os.path.join(UPLOAD_FOLDER, nome_arquivo)

        # Salvar arquivo
        arquivo.save(caminho_completo)

        # Criar registro no banco
        anexo = AnexoProntuario(
            paciente_id=paciente_id,
            nome_arquivo=nome_arquivo,
            nome_original=nome_original,
            tipo_arquivo=arquivo.content_type,
            tamanho=file_size,
            descricao=request.form.get('descricao', ''),
            usuario_upload=request.form.get('usuario', 'Sistema')
        )

        db.session.add(anexo)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Arquivo enviado com sucesso!',
            'anexo': {
                'id': anexo.id,
                'nome_original': anexo.nome_original,
                'tamanho': get_file_size_str(file_size),
                'data_upload': anexo.data_upload.strftime('%d/%m/%Y %H:%M')
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@anexos_bp.route('/download/<int:anexo_id>')
def download_anexo(anexo_id):
    """Baixa um arquivo anexo"""
    try:
        anexo = AnexoProntuario.query.get_or_404(anexo_id)
        caminho_arquivo = os.path.join(UPLOAD_FOLDER, anexo.nome_arquivo)

        if not os.path.exists(caminho_arquivo):
            flash('Arquivo não encontrado no servidor', 'error')
            return redirect(request.referrer or url_for('prontuario.lista_pacientes'))

        return send_file(
            caminho_arquivo,
            as_attachment=True,
            download_name=anexo.nome_original
        )

    except Exception as e:
        flash(f'Erro ao baixar arquivo: {str(e)}', 'error')
        return redirect(request.referrer or url_for('prontuario.lista_pacientes'))

@anexos_bp.route('/deletar/<int:anexo_id>', methods=['POST'])
def deletar_anexo(anexo_id):
    """Deleta um arquivo anexo"""
    try:
        anexo = AnexoProntuario.query.get_or_404(anexo_id)
        caminho_arquivo = os.path.join(UPLOAD_FOLDER, anexo.nome_arquivo)

        # Deletar arquivo físico
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)

        # Deletar registro do banco
        db.session.delete(anexo)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Arquivo deletado com sucesso'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

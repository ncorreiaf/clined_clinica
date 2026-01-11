"""
Script para migrar anexos existentes do sistema de arquivos para o banco de dados

Este script:
1. Busca todos os anexos no banco que não têm arquivo_binario
2. Localiza o arquivo físico correspondente em uploads/anexos
3. Lê o arquivo e salva o conteúdo binário no banco
4. Gera relatório de sucesso e falhas
"""

import os
import sys
from datetime import datetime

from app import create_app, db
from models.models import AnexoProntuario

UPLOAD_FOLDER = 'uploads/anexos'

def migrar_anexos():
    """Migra arquivos do sistema de arquivos para o banco de dados"""

    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("MIGRAÇÃO DE ANEXOS PARA O BANCO DE DADOS")
        print("=" * 60)
        print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print()

        # Buscar anexos sem arquivo binário
        anexos = AnexoProntuario.query.filter(
            (AnexoProntuario.arquivo_binario == None) |
            (AnexoProntuario.arquivo_binario == b'')
        ).all()

        print(f"Total de anexos encontrados sem arquivo binário: {len(anexos)}")
        print()

        if len(anexos) == 0:
            print("Nenhum anexo precisa ser migrado.")
            print("=" * 60)
            return

        sucesso = 0
        falhas = 0
        falhas_detalhes = []

        for anexo in anexos:
            try:
                # Montar caminho do arquivo físico
                caminho_arquivo = os.path.join(UPLOAD_FOLDER, anexo.nome_arquivo)

                if not os.path.exists(caminho_arquivo):
                    falhas += 1
                    erro = f"Arquivo físico não encontrado: {caminho_arquivo}"
                    falhas_detalhes.append({
                        'id': anexo.id,
                        'paciente_id': anexo.paciente_id,
                        'nome_original': anexo.nome_original,
                        'erro': erro
                    })
                    print(f"❌ Anexo ID {anexo.id}: {erro}")
                    continue

                # Ler arquivo em binário
                with open(caminho_arquivo, 'rb') as f:
                    arquivo_bytes = f.read()

                # Atualizar o registro no banco
                anexo.arquivo_binario = arquivo_bytes

                # Verificar/atualizar tamanho se necessário
                if not anexo.tamanho:
                    anexo.tamanho = len(arquivo_bytes)

                db.session.add(anexo)
                sucesso += 1
                print(f"✓ Anexo ID {anexo.id} migrado: {anexo.nome_original} ({len(arquivo_bytes)} bytes)")

            except Exception as e:
                falhas += 1
                falhas_detalhes.append({
                    'id': anexo.id,
                    'paciente_id': anexo.paciente_id,
                    'nome_original': anexo.nome_original,
                    'erro': str(e)
                })
                print(f"❌ Erro ao migrar anexo ID {anexo.id}: {str(e)}")

        # Commitar todas as mudanças
        if sucesso > 0:
            try:
                db.session.commit()
                print()
                print(f"✓ {sucesso} anexo(s) migrado(s) com sucesso!")
            except Exception as e:
                db.session.rollback()
                print()
                print(f"❌ Erro ao salvar no banco: {str(e)}")
                print("Todas as alterações foram revertidas.")
                return

        # Relatório final
        print()
        print("=" * 60)
        print("RELATÓRIO FINAL")
        print("=" * 60)
        print(f"Total processado: {len(anexos)}")
        print(f"Sucesso: {sucesso}")
        print(f"Falhas: {falhas}")

        if falhas > 0:
            print()
            print("DETALHES DAS FALHAS:")
            print("-" * 60)
            for falha in falhas_detalhes:
                print(f"ID: {falha['id']} | Paciente: {falha['paciente_id']} | Arquivo: {falha['nome_original']}")
                print(f"  Erro: {falha['erro']}")
                print()

        print("=" * 60)

        # Informação adicional sobre arquivos físicos
        if sucesso > 0:
            print()
            print("OBSERVAÇÃO:")
            print("Os arquivos físicos em 'uploads/anexos' podem ser removidos manualmente")
            print("após confirmar que a migração foi bem-sucedida e que os anexos")
            print("estão acessíveis através do sistema.")
            print()

if __name__ == '__main__':
    try:
        migrar_anexos()
    except Exception as e:
        print(f"Erro crítico durante a migração: {str(e)}")
        sys.exit(1)

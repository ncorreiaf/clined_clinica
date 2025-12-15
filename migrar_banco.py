"""
Script para migrar o banco de dados sem perder dados
Corrige o problema de CPF obrigatório para opcional
"""

import sqlite3
import os
import shutil
from datetime import datetime

def migrar_banco():
    """
    Migra o banco de dados alterando a constraint do CPF
    """
    db_path = 'instance/clined.db'

    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado!")
        return

    # Fazer backup
    backup_path = f'instance/clined_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    print(f"📦 Criando backup: {backup_path}")
    shutil.copy2(db_path, backup_path)

    # Conectar ao banco
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("🔧 Iniciando migração...")

        # Verificar estrutura atual
        cursor.execute("PRAGMA table_info(pacientes)")
        colunas = cursor.fetchall()
        print(f"📋 Estrutura atual da tabela 'pacientes': {len(colunas)} colunas")

        # Criar nova tabela com estrutura correta
        print("📝 Criando nova tabela temporária...")
        cursor.execute("""
            CREATE TABLE pacientes_novo (
                id INTEGER PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                cpf VARCHAR(14) UNIQUE,
                telefone VARCHAR(20) NOT NULL,
                email VARCHAR(100),
                data_nascimento DATE,
                idade INTEGER,
                naturalidade VARCHAR(100),
                estado_civil VARCHAR(50),
                religiao VARCHAR(50),
                profissao VARCHAR(100),
                filiacao_pai VARCHAR(100),
                filiacao_mae VARCHAR(100),
                endereco TEXT,
                bairro VARCHAR(100),
                cidade VARCHAR(100),
                data_cadastro DATETIME
            )
        """)

        # Copiar dados da tabela antiga para a nova
        print("📤 Copiando dados...")
        cursor.execute("""
            INSERT INTO pacientes_novo
            SELECT * FROM pacientes
        """)

        rows_copied = cursor.rowcount
        print(f"✅ {rows_copied} registros copiados")

        # Remover tabela antiga
        print("🗑️  Removendo tabela antiga...")
        cursor.execute("DROP TABLE pacientes")

        # Renomear nova tabela
        print("✏️  Renomeando nova tabela...")
        cursor.execute("ALTER TABLE pacientes_novo RENAME TO pacientes")

        # Commit das mudanças
        conn.commit()

        print("\n" + "="*60)
        print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*60)
        print(f"\n📦 Backup salvo em: {backup_path}")
        print(f"📊 Pacientes migrados: {rows_copied}")
        print("\n✨ Agora o CPF é opcional e você pode cadastrar pacientes sem CPF!")
        print("="*60)

    except Exception as e:
        print(f"\n❌ ERRO na migração: {str(e)}")
        print(f"📦 Seus dados estão seguros no backup: {backup_path}")
        conn.rollback()

    finally:
        conn.close()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🔧 MIGRAÇÃO DO BANCO DE DADOS")
    print("="*60)
    print("\nEste script vai:")
    print("  ✓ Criar um backup do banco atual")
    print("  ✓ Alterar a estrutura para tornar CPF opcional")
    print("  ✓ Preservar todos os dados existentes")
    print("\n" + "="*60)

    resposta = input("\nDeseja continuar? (sim/não): ")

    if resposta.lower() in ['sim', 's', 'yes', 'y']:
        migrar_banco()
    else:
        print("❌ Operação cancelada.")

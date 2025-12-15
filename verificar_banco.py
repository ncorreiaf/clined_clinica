"""
Script para verificar o estado atual do banco de dados
"""

from app import app, db
from models.models import Paciente, Usuario, Agendamento

def verificar_banco():
    """
    Verifica e exibe o estado atual do banco de dados
    """
    with app.app_context():
        print("\n" + "="*60)
        print("🔍 VERIFICAÇÃO DO BANCO DE DADOS")
        print("="*60)

        # Verificar pacientes
        print("\n👥 PACIENTES:")
        print("-"*60)
        pacientes = Paciente.query.all()
        print(f"Total: {len(pacientes)} pacientes\n")

        if pacientes:
            for p in pacientes:
                print(f"ID: {p.id}")
                print(f"  Nome: {p.nome}")
                print(f"  CPF: {p.cpf or '(não informado)'}")
                print(f"  Telefone: {p.telefone}")
                print(f"  Email: {p.email or '(não informado)'}")

                # Contar agendamentos deste paciente
                agendamentos = Agendamento.query.filter_by(paciente_id=p.id).count()
                print(f"  Agendamentos: {agendamentos}")
                print()
        else:
            print("  Nenhum paciente cadastrado\n")

        # Verificar usuários
        print("\n👤 USUÁRIOS DO SISTEMA:")
        print("-"*60)
        usuarios = Usuario.query.all()
        print(f"Total: {len(usuarios)} usuários\n")

        if usuarios:
            for u in usuarios:
                print(f"ID: {u.id}")
                print(f"  Nome: {u.nome}")
                print(f"  Email: {u.email}")
                print(f"  Perfil: {u.perfil}")
                print(f"  Ativo: {'Sim' if u.ativo else 'Não'}")
                print()
        else:
            print("  Nenhum usuário cadastrado\n")

        # Verificar agendamentos
        print("\n📅 AGENDAMENTOS:")
        print("-"*60)
        agendamentos = Agendamento.query.all()
        print(f"Total: {len(agendamentos)} agendamentos\n")

        if agendamentos:
            for a in agendamentos:
                paciente = Paciente.query.get(a.paciente_id)
                print(f"ID: {a.id}")
                print(f"  Paciente: {paciente.nome if paciente else 'PACIENTE NÃO ENCONTRADO!'}")
                print(f"  Serviço: {a.servico}")
                print(f"  Data: {a.data_agendamento.strftime('%d/%m/%Y %H:%M')}")
                print(f"  Status: {a.status}")
                print()

        print("="*60)

if __name__ == '__main__':
    verificar_banco()

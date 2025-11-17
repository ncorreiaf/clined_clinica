# Mudanças Realizadas no Sistema CLINED

## Resumo das Alterações

O sistema foi adaptado para refletir a realidade da clínica CLINED com as seguintes mudanças principais:

### 1. Configuração da Clínica
- **Profissional Único**: Dr. Darllan (único médico da clínica)
- **CRM**: CRM-AL XXXXX (configurável em config.py)
- **CNPJ**: 17505453/000172

### 2. Serviços Disponíveis
O sistema agora oferece os seguintes serviços:
- Consulta Médica
- Eletroencefalograma
- Eletrocardiograma
- Mapa Holter
- Ecocardiograma
- Ultrassonografia

### 3. Novos Modelos de Documentos Médicos

#### Receituário (Receituario)
- Prescrição de medicamentos
- Posologia e observações
- Validade do receituário

#### Laudo (Laudo)
- Relatórios de exames
- Conclusões médicas
- Tipo de exame realizado

#### Atestado (Atestado)
- Atestados médicos
- CID
- Dias de afastamento
- Período de validade

#### Recibo (Recibo)
- Gerado no momento do agendamento
- Número único de recibo
- Forma de pagamento
- Valor do serviço

### 4. Simplificações Realizadas

#### Agendamento
- Removida seleção de profissional (sempre Dr. Darllan)
- Campo de serviço adaptado para lista dos exames disponíveis
- Adicionado campo de email

#### Dados Iniciais
- Sistema cria apenas o Dr. Darllan
- Removidos profissionais múltiplos do banco

### 5. Novas Rotas

Criado novo blueprint `documentos_bp` com as seguintes rotas:

- `/documentos/receituario/<prontuario_id>` - Gerar receituário
- `/documentos/laudo/<prontuario_id>` - Gerar laudo
- `/documentos/atestado/<prontuario_id>` - Gerar atestado
- `/documentos/recibo/<agendamento_id>` - Gerar recibo
- `/documentos/pedido-exame/<prontuario_id>` - Gerar pedido de exame

### 6. Arquivos Modificados

1. **models/models.py**
   - Adicionados modelos: Receituario, Laudo, Atestado, Recibo
   - Atualizado SolicitacaoExame com novos campos

2. **config.py**
   - Adicionadas configurações do Dr. Darllan
   - Lista de serviços disponíveis
   - Informações da clínica

3. **app.py**
   - Importados novos modelos
   - Registrado blueprint de documentos
   - Atualizada função criar_dados_iniciais()

4. **routes/agendamento.py**
   - Simplificada rota de agendamento
   - Removida seleção de profissional
   - Busca automática do Dr. Darllan

5. **routes/documentos.py** (NOVO)
   - Rotas para todos os documentos médicos
   - Integração com prontuários e agendamentos

6. **templates/agendamento/agendar.html**
   - Removido select de profissional
   - Exibe Dr. Darllan automaticamente
   - Lista de serviços dinâmica

### 7. Próximos Passos para Implementação Completa

1. Criar templates HTML para documentos:
   - templates/documentos/receituario.html
   - templates/documentos/laudo.html
   - templates/documentos/atestado.html
   - templates/documentos/recibo.html
   - templates/documentos/pedido_exame.html

2. Atualizar template ver_prontuario.html:
   - Adicionar botões para gerar documentos
   - Seção "Documentos Médicos" com links

3. Remover funcionalidades desnecessárias:
   - Simplificar repasses (não há mais múltiplos profissionais)
   - Ajustar relatórios para um único médico

## Como Usar

### Agendamento
1. Acesse "Novo Agendamento"
2. Preencha dados do paciente
3. Selecione data/hora e o serviço/exame
4. Sistema atribuirá automaticamente ao Dr. Darllan
5. Após confirmar, pode gerar recibo

### Prontuário
1. Acesse o prontuário do paciente
2. Crie nova entrada de atendimento
3. Após salvar, gere documentos:
   - Receituário para prescrições
   - Laudo para resultados de exames
   - Atestado se necessário
   - Pedido de exame para solicitar novos exames

### Recibo
1. Na lista de agendamentos
2. Clique em "Gerar Recibo"
3. Informe valor e forma de pagamento
4. Imprima ou salve em PDF

## Configurações Importantes

Edite `/config.py` para ajustar:
- CRM do Dr. Darllan
- Horários de funcionamento
- Lista de serviços/exames
- CNPJ da clínica

## Banco de Dados

Ao iniciar o sistema pela primeira vez:
1. Delete o arquivo `database.db` se existir
2. Execute `python app.py`
3. Sistema criará novo banco com Dr. Darllan


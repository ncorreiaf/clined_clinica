# Sistema de Autenticação e Controle de Acesso - CLINED

## Visão Geral

O sistema CLINED agora possui um robusto sistema de autenticação multi-perfil que integra Supabase (PostgreSQL) para gerenciamento de usuários com Flask para a lógica de aplicação.

## Arquitetura do Sistema

### Tecnologias Utilizadas

- **Backend**: Flask 2.3.3 + SQLAlchemy 2.0.23
- **Banco de Dados de Usuários**: Supabase (PostgreSQL)
- **Banco de Dados da Aplicação**: SQLite (agendamentos, prontuários, etc)
- **Autenticação**: Sessões customizadas com bcrypt para hashing de senhas
- **Bibliotecas**: Flask-Login 0.6.3, supabase-py 2.3.0, bcrypt 4.1.2

### Estrutura de Dados no Supabase

#### Tabela `usuarios`
- `id` (uuid): Identificador único
- `email` (text): Email para login
- `senha_hash` (text): Senha criptografada com bcrypt
- `nome` (text): Nome completo
- `perfil` (text): 'admin', 'medico' ou 'tv'
- `ativo` (boolean): Status do usuário
- `profissional_id` (integer): Vínculo com profissional no SQLite
- `ultimo_acesso` (timestamptz): Data do último login
- `token_tv` (text): Token único para acesso ao painel de TV
- `created_at` (timestamptz): Data de criação

#### Tabela `sessoes_usuario`
- `id` (uuid): Identificador único
- `usuario_id` (uuid): Referência ao usuário
- `token_sessao` (text): Token da sessão
- `ip_address` (text): IP do usuário
- `user_agent` (text): Navegador/dispositivo
- `expira_em` (timestamptz): Data de expiração (24h)
- `created_at` (timestamptz): Data de criação

#### Tabela `logs_acesso`
- `id` (uuid): Identificador único
- `usuario_id` (uuid): Referência ao usuário
- `acao` (text): 'login', 'logout', 'acesso_negado', etc
- `ip_address` (text): IP do usuário
- `user_agent` (text): Navegador/dispositivo
- `detalhes` (jsonb): Informações adicionais
- `sucesso` (boolean): Status da ação
- `created_at` (timestamptz): Data da ação

## Perfis de Acesso

### 1. Administrador (admin)

**Acesso Completo ao Sistema**

**Funcionalidades:**
- ✅ Dashboard administrativo com estatísticas gerais
- ✅ Gerenciamento de agendamentos (criar, editar, visualizar)
- ✅ Acesso total a prontuários de todos os pacientes
- ✅ Módulo financeiro completo (contas a pagar/receber, fluxo de caixa)
- ✅ Relatórios e indicadores (faturamento, ticket médio, NPS)
- ✅ Configuração de metas empresariais
- ✅ Geração de documentos médicos
- ✅ Gerenciamento de usuários (criar, editar, desativar)
- ✅ Visualização de logs de auditoria
- ✅ Acesso ao painel de TV

**Credenciais Padrão:**
- Email: `admin@clined.com.br`
- Senha: `admin123`

### 2. Médico (medico)

**Acesso Focado em Atendimento Clínico**

**Funcionalidades:**
- ✅ Dashboard médico personalizado
- ✅ Visualização de agendamentos do dia
- ✅ Fila de espera em tempo real
- ✅ Acesso completo a prontuários (visualizar, criar, editar)
- ✅ Geração de documentos médicos:
  - Receituários
  - Laudos médicos
  - Atestados
  - Solicitações de exames
  - Recibos
- ✅ Visualização de anexos dos pacientes
- ✅ Atualização de status de atendimento
- ✅ Acesso ao painel de TV
- ❌ Módulo financeiro (valores, pagamentos)
- ❌ Metas empresariais
- ❌ Relatórios administrativos (faturamento, ticket médio)
- ❌ Gerenciamento de usuários

**Credenciais Padrão:**
- Email: `darlan@clined.com.br`
- Senha: `medico123`
- Vinculado ao: Dr. Darlan Medeiros (Psiquiatria)

### 3. Painel de TV (tv)

**Acesso Público Limitado para Visualização**

**Funcionalidades:**
- ✅ Visualização em tempo real dos atendimentos
- ✅ Exibição do atendimento atual
- ✅ Lista dos próximos atendimentos
- ✅ Estatísticas do dia
- ✅ Informações do profissional de plantão
- ✅ Auto-atualização a cada 5 segundos
- ❌ Não requer login tradicional (usa token na URL)
- ❌ Modo somente leitura

**Acesso:**
O token único será gerado automaticamente na primeira execução do sistema e exibido no console. Para acessar o painel:

```
http://localhost:5000/chamados/painel-tv?token=SEU_TOKEN_AQUI
```

## Instalação e Configuração

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente

O arquivo `.env` já está configurado com as credenciais do Supabase:

```
SUPABASE_URL=https://durprqxostdiphdmjamh.supabase.co
SUPABASE_ANON_KEY=...
```

### 3. Inicializar o Sistema

```bash
python app.py
```

Na primeira execução, o sistema irá:
1. Criar as tabelas no SQLite (agendamentos, prontuários, etc)
2. Criar as tabelas no Supabase (usuários, sessões, logs)
3. Cadastrar o Dr. Darlan como profissional
4. Criar os usuários iniciais (admin, médico, tv)
5. Exibir as credenciais e o token de TV no console

## Fluxo de Autenticação

### 1. Login
1. Usuário acessa `/auth/login`
2. Insere email e senha
3. Sistema valida credenciais no Supabase
4. Cria sessão com expiração de 24h
5. Redireciona para dashboard apropriado:
   - Admin → Dashboard administrativo
   - Médico → Dashboard médico

### 2. Sessão
- Armazenada no Supabase com token único
- Validade de 24 horas
- Atualiza `ultimo_acesso` do usuário
- Registra log de acesso

### 3. Logout
- Remove sessão do Supabase
- Limpa session do Flask
- Registra log de logout
- Redireciona para página de login

### 4. Proteção de Rotas

Três tipos de decoradores:

```python
@login_required
Requer autenticação (qualquer perfil)

@medico_required
Requer perfil médico ou admin

@admin_required
Requer perfil admin apenas
```

## Funcionalidades de Segurança

### 1. Hashing de Senhas
- Algoritmo: bcrypt
- Salt gerado automaticamente
- Senhas nunca armazenadas em texto plano

### 2. Controle de Sessão
- Tokens únicos e seguros (secrets.token_urlsafe)
- Expiração automática após 24h
- Limpeza de sessões expiradas
- Validação a cada requisição

### 3. Row Level Security (RLS)
- Políticas restritivas no Supabase
- Usuários só acessam seus próprios dados
- Admins têm acesso completo
- Isolamento entre perfis

### 4. Logs de Auditoria
- Todas as ações são registradas
- Rastreamento de IP e user-agent
- Histórico de tentativas de login
- Detalhes de ações administrativas

### 5. Proteção CSRF
- Implementada via session do Flask
- Validação em todos os formulários

## Gerenciamento de Usuários (Admin)

### Criar Novo Usuário

1. Acessar: `/admin/usuarios`
2. Clicar em "Novo Usuário"
3. Preencher:
   - Nome completo
   - Email
   - Senha (mínimo 6 caracteres)
   - Perfil (admin/medico/tv)
   - ID do Profissional (opcional, para médicos)
4. Salvar

**Nota:** Para perfil TV, um token único é gerado automaticamente.

### Editar Usuário

1. Acessar: `/admin/usuarios`
2. Clicar no botão "Editar" do usuário
3. Modificar:
   - Nome
   - Email
   - Status (ativo/inativo)
   - Senha (opcional)
4. Salvar

### Desativar Usuário

1. Acessar: `/admin/usuarios`
2. Clicar no botão "Desativar"
3. Confirmar ação

**Nota:** Usuários desativados não podem fazer login.

## Logs de Acesso (Admin)

Visualizar histórico completo de acessos:

- `/admin/logs`
- Exibe últimos 100 logs
- Informações: data/hora, usuário, ação, IP, status, detalhes

## Personalização do Perfil

Todos os usuários podem:

1. Ver informações do perfil: `/auth/perfil`
2. Alterar senha: `/auth/alterar-senha`
3. Visualizar últimos acessos

## Interface Adaptativa

A navegação lateral adapta-se automaticamente ao perfil:

### Admin
- Dashboard
- Agendamentos
- Prontuários
- Financeiro
- Relatórios
- Metas
- Painel de TV
- Administração (Usuários, Logs)

### Médico
- Dashboard Médico
- Agendamentos
- Prontuários
- Painel de TV

### TV
- Sem navegação (tela cheia)

## Boas Práticas

### Para Administradores
1. Altere a senha padrão imediatamente
2. Crie senhas fortes (mínimo 8 caracteres, letras, números e símbolos)
3. Revise logs de acesso regularmente
4. Desative usuários inativos
5. Não compartilhe credenciais

### Para Médicos
1. Faça logout ao sair do consultório
2. Não compartilhe senha com recepção
3. Mantenha prontuários atualizados
4. Use documentos adequados para cada situação

### Para o Sistema
1. Mantenha o Supabase URL e Key seguros
2. Não exponha tokens de TV publicamente
3. Faça backup regular do banco SQLite
4. Monitore logs de erro

## Solução de Problemas

### "Token de acesso não fornecido" no Painel de TV
- Verifique se o token está na URL
- Copie o token exato do console ao iniciar o sistema
- Formato: `/chamados/painel-tv?token=TOKEN_AQUI`

### "Email ou senha incorretos"
- Verifique se o usuário está ativo
- Confirme o email (case-sensitive)
- Tente redefinir a senha (admin)

### Sessão expira muito rápido
- Sessões duram 24h por padrão
- Verifique se há erro de conexão com Supabase
- Logs podem indicar problema de autenticação

### Erro ao conectar no Supabase
- Verifique variáveis no `.env`
- Confirme que o Supabase está acessível
- Teste conexão: `python -c "from utils.supabase_client import supabase; print(supabase)"`

## Estrutura de Arquivos

```
project/
├── utils/
│   ├── __init__.py
│   ├── supabase_client.py      # Cliente Supabase
│   └── auth_helpers.py          # Funções de autenticação
├── routes/
│   ├── auth.py                  # Rotas de autenticação
│   ├── medico.py                # Dashboard médico
│   ├── admin.py                 # Gestão de usuários
│   ├── agendamento.py          # (protegido)
│   ├── prontuario.py           # (protegido)
│   ├── financeiro.py           # (protegido - admin only)
│   ├── relatorios.py           # (protegido - admin only)
│   └── chamados.py             # Painel TV (token)
├── templates/
│   ├── auth/
│   │   ├── login.html
│   │   ├── perfil.html
│   │   └── alterar_senha.html
│   ├── medico/
│   │   └── dashboard.html
│   └── admin/
│       ├── usuarios.html
│       ├── novo_usuario.html
│       ├── editar_usuario.html
│       └── logs.html
├── .env                         # Configurações Supabase
└── requirements.txt             # Dependências Python
```

## Próximos Passos Recomendados

1. **Produção**:
   - Configurar HTTPS
   - Usar secrets manager para variáveis sensíveis
   - Implementar rate limiting
   - Adicionar autenticação de dois fatores (2FA)

2. **Funcionalidades**:
   - Recuperação de senha por email
   - Notificações em tempo real
   - Auditoria avançada com filtros
   - Exportação de logs

3. **Melhorias de UX**:
   - Lembrar último login
   - Modo escuro
   - Atalhos de teclado
   - Tour guiado para novos usuários

## Suporte

Para dúvidas ou problemas:
- Verifique os logs de erro no console
- Consulte os logs de acesso no admin
- Revise esta documentação
- Entre em contato com o desenvolvedor do sistema

---

**CLINED - Um novo conceito em saúde**
Sistema de Gestão Clínica com Controle de Acesso Multi-Perfil
CNPJ: 17505453/000172

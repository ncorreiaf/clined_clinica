# 🚀 Guia de Deploy no Render

Este guia explica passo a passo como publicar o Sistema CLINED no Render.

## 📋 Pré-requisitos

1. Conta no GitHub (para hospedar o código)
2. Conta no Render (gratuita) - https://render.com

## 🔧 Preparação (JÁ FEITO!)

Os seguintes arquivos já foram criados e configurados:

✅ `render.yaml` - Configuração automática do Render
✅ `build.sh` - Script de build e instalação
✅ `Procfile` - Comando para iniciar a aplicação
✅ `runtime.txt` - Versão do Python
✅ `requirements.txt` - Dependências atualizadas
✅ `config.py` - Suporte a PostgreSQL
✅ `.gitignore` - Arquivos a serem ignorados

## 📤 Passo 1: Subir o Código para o GitHub

Se ainda não tem um repositório Git, crie um:

```bash
cd /caminho/do/seu/projeto
git init
git add .
git commit -m "Preparar projeto para deploy no Render"
```

Crie um repositório no GitHub e suba o código:

```bash
git remote add origin https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
git branch -M main
git push -u origin main
```

## 🌐 Passo 2: Criar Conta no Render

1. Acesse https://render.com
2. Clique em "Get Started" ou "Sign Up"
3. Faça login com sua conta do GitHub
4. Autorize o Render a acessar seus repositórios

## 🎯 Passo 3: Deploy no Render

### Opção A: Deploy Automático (Recomendado)

O Render vai detectar automaticamente o arquivo `render.yaml` e configurar tudo:

1. No dashboard do Render, clique em **"New +"**
2. Selecione **"Blueprint"**
3. Conecte seu repositório do GitHub
4. O Render vai ler o `render.yaml` e criar:
   - Web Service (aplicação Flask)
   - PostgreSQL Database (banco de dados gratuito)
5. Clique em **"Apply"**
6. Aguarde o build (leva 3-5 minutos)

### Opção B: Deploy Manual

Se preferir configurar manualmente:

#### 3.1 Criar o Banco de Dados PostgreSQL

1. No dashboard, clique em **"New +"** → **"PostgreSQL"**
2. Preencha:
   - **Name**: `clined-db`
   - **Database**: `clined`
   - **User**: `clined`
   - **Region**: Oregon (Free)
   - **Instance Type**: Free
3. Clique em **"Create Database"**
4. Aguarde a criação (1-2 minutos)
5. **Copie a "Internal Database URL"** - você vai precisar!

#### 3.2 Criar o Web Service

1. No dashboard, clique em **"New +"** → **"Web Service"**
2. Conecte seu repositório do GitHub
3. Configure:
   - **Name**: `clined-system` (ou o nome que preferir)
   - **Region**: Oregon (Free)
   - **Branch**: `main`
   - **Runtime**: Python 3
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free

#### 3.3 Configurar Variáveis de Ambiente

Na seção "Environment", adicione:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | Cole a Internal Database URL do PostgreSQL |
| `SECRET_KEY` | Clique em "Generate" para criar uma chave aleatória |
| `FLASK_ENV` | `production` |
| `DEBUG` | `false` |

4. Clique em **"Create Web Service"**
5. Aguarde o build e deploy (3-5 minutos)

## ✅ Passo 4: Verificar o Deploy

1. Quando o deploy terminar, você verá **"Live"** em verde
2. Clique na URL fornecida (ex: `https://clined-system.onrender.com`)
3. O sistema deve abrir a página de login

**Credenciais iniciais:**
- Admin: `admin@clined.com.br` / `admin123`
- Médico: `darlan@clined.com.br` / `medico123`

## 🔄 Atualizações Futuras

Toda vez que você fizer push para o GitHub, o Render vai:
1. Detectar as mudanças automaticamente
2. Fazer rebuild da aplicação
3. Publicar a nova versão

```bash
git add .
git commit -m "Descrição das mudanças"
git push origin main
```

## 📊 Monitoramento

No dashboard do Render você pode:
- Ver logs em tempo real
- Monitorar uso de recursos
- Verificar status do banco de dados
- Acompanhar deploys anteriores

## ⚠️ Observações Importantes

### Plano Gratuito do Render

- ✅ 750 horas gratuitas por mês
- ✅ PostgreSQL com 1GB de armazenamento
- ⚠️ Aplicação "hiberna" após 15 minutos de inatividade
- ⚠️ Primeiro acesso após hibernação leva ~30 segundos

### Limitações

- O banco SQLite local NÃO será usado em produção
- Os dados do SQLite local NÃO serão migrados automaticamente
- Você precisará cadastrar novos dados no PostgreSQL

### Banco de Dados

O sistema vai criar automaticamente todas as tabelas no PostgreSQL na primeira execução. Os dados iniciais (Dr. Darlan Medeiros e usuários) serão criados automaticamente.

## 🆘 Problemas Comuns

### Build falhou

- Verifique os logs no Render
- Certifique-se que todos os arquivos estão no GitHub
- Confirme que o `build.sh` tem permissão de execução

### Erro de conexão com banco

- Verifique se a variável `DATABASE_URL` está configurada
- Confirme que o banco de dados está "Available" no Render
- Veja os logs para detalhes do erro

### Aplicação não inicia

- Verifique o Start Command: `gunicorn app:app`
- Confirme que todas as variáveis de ambiente estão configuradas
- Revise os logs de inicialização

## 📞 Suporte

- Documentação do Render: https://render.com/docs
- Status do Render: https://status.render.com

---

**Pronto!** Seu sistema CLINED está agora na nuvem e acessível de qualquer lugar! 🎉

# SorteiaPro — Sistema de Sorteio do Tribunal Regional

Backend completo para gerenciamento de processos judiciais com sorteio
automático de juízes, controle de conflitos de interesse e auditoria integral.

---

## 1. Descrição do Sistema

O **SorteiaPro** automatiza a distribuição de processos judiciais entre juízes
de forma imparcial, rastreável e auditável. Principais funcionalidades:

- **Sorteio automático** via APScheduler (seg–sex às 10:00, horário de Brasília)
- **Rodízio obrigatório** para processos COMPLEX (todos os 8 juízes participam antes de reiniciar)
- **Balanceamento de carga** com alertas quando a diferença de pesos ultrapassa 3 pontos
- **Sorteio certeiro** (prioridade ao juiz que recusou um processo do mesmo nível)
- **Controle de conflitos de interesse** com registro de documentos
- **Juiz temporário** para casos em que todos os titulares recusaram
- **RBAC completo** (TI, JUDGE, ASSESSOR, ASSISTANT, TEMP_JUDGE)
- **Auditoria append-only** de todas as ações
- **Swagger UI** em `/docs`

---

## 2. Pré-requisitos

| Requisito | Versão mínima |
|-----------|---------------|
| Python    | 3.12+         |
| PostgreSQL | 14+          |
| pip       | 23+           |

---

## 3. Passo a Passo de Instalação

### 3.1 Clone e entre na pasta do projeto

```bash
cd sorteiapro
```

### 3.2 Crie e ative um ambiente virtual

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 3.3 Instale as dependências

```bash
pip install -r requirements.txt
```

### 3.4 Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o arquivo `.env` com os dados do seu PostgreSQL:

```env
DATABASE_URL=postgresql+asyncpg://SEU_USER:SUA_SENHA@localhost:5432/sorteiapro
SYNC_DATABASE_URL=postgresql://SEU_USER:SUA_SENHA@localhost:5432/sorteiapro
SECRET_KEY=uma-chave-secreta-longa-e-aleatoria
```

### 3.5 Crie o banco de dados no PostgreSQL

```sql
CREATE DATABASE sorteiapro;
```

### 3.6 Execute as migrations

```bash
alembic upgrade head
```

> Se ainda não existe migration, gere uma primeiro:
> ```bash
> alembic revision --autogenerate -m "initial"
> alembic upgrade head
> ```

### 3.7 Popule os dados iniciais

```bash
python seed.py
```

---

## 4. Variáveis de Ambiente

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `DATABASE_URL` | URL async (asyncpg) para a aplicação | `postgresql+asyncpg://user:pass@localhost:5432/sorteiapro` |
| `SYNC_DATABASE_URL` | URL síncrona (psycopg2) para o Alembic | `postgresql://user:pass@localhost:5432/sorteiapro` |
| `SECRET_KEY` | Chave para assinar tokens JWT | `minha-chave-super-secreta` |
| `ALGORITHM` | Algoritmo JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_HOURS` | Expiração do token (horas) | `8` |
| `UPLOAD_DIR` | Diretório para documentos de conflito | `./uploads` |
| `ENVIRONMENT` | Ambiente atual | `development` / `production` |

---

## 5. Como Executar

```bash
uvicorn app.main:app --reload --port 8000
```

Acesse:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Healthcheck:** http://localhost:8000/health

---

## 6. Exemplos de Chamadas à API

> Substitua `TOKEN` pelo token retornado no login.

### 6.1 Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=ti@tribunal.gov.br&password=Admin@2025"
```

**Resposta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 28800
}
```

---

### 6.2 Cadastrar uma Pessoa (parte do processo)

```bash
curl -X POST http://localhost:8000/conflicts/pre-register \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "judge_id": "UUID-DO-JUIZ",
    "person_id": "UUID-DA-PESSOA",
    "reason": "Parente de primeiro grau"
  }'
```

---

### 6.3 Cadastrar Processo

Primeiro, crie uma Person via Swagger UI ou diretamente no banco.
Em seguida:

```bash
curl -X POST http://localhost:8000/processes/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "process_number": "0001234-56.2024.8.06.0001",
    "level": 1,
    "person_id": "UUID-DA-PESSOA"
  }'
```

**Resposta:**
```json
{
  "id": "uuid-do-processo",
  "process_number": "0001234-56.2024.8.06.0001",
  "level": 1,
  "status": "PENDING_LOTTERY",
  "lottery_scheduled_at": "2024-01-15T10:00:00",
  ...
}
```

---

### 6.4 Forçar Sorteio Manual (teste)

```bash
curl -X POST http://localhost:8000/processes/UUID-DO-PROCESSO/run-lottery \
  -H "Authorization: Bearer TOKEN"
```

**Resposta:**
```json
{
  "detail": "Sorteio executado com sucesso",
  "process_id": "uuid-do-processo",
  "new_status": "ASSIGNED",
  "assigned_judge_id": "uuid-do-juiz-sorteado"
}
```

---

### 6.5 Registrar Conflito de Interesse (Juiz recusa processo)

```bash
# Login como juiz primeiro
curl -X POST http://localhost:8000/auth/login \
  -d "username=judge01@tribunal.gov.br&password=Judge@2025"

# Recusar o processo (multipart/form-data com documento)
curl -X POST http://localhost:8000/conflicts/refuse \
  -H "Authorization: Bearer TOKEN_DO_JUIZ" \
  -F "process_id=UUID-DO-PROCESSO" \
  -F "justification=Tenho relação pessoal com a parte envolvida no processo." \
  -F "document=@/caminho/para/documento.pdf"
```

---

### 6.6 Nomear Juiz Temporário (quando todos recusaram)

```bash
curl -X POST http://localhost:8000/conflicts/assign-temp-judge \
  -H "Authorization: Bearer TOKEN_TI" \
  -H "Content-Type: application/json" \
  -d '{
    "process_id": "UUID-DO-PROCESSO",
    "temp_judge_user_id": "UUID-DO-JUIZ-TEMPORARIO"
  }'
```

---

### 6.7 Visualizar Logs de Auditoria

```bash
# Todos os logs (TI apenas)
curl http://localhost:8000/audit/logs \
  -H "Authorization: Bearer TOKEN_TI"

# Logs de um processo específico
curl http://localhost:8000/audit/logs/process/UUID-DO-PROCESSO \
  -H "Authorization: Bearer TOKEN_TI"
```

---

## 7. Estrutura de Pastas

```
sorteiapro/
├── alembic/
│   ├── versions/          # Arquivos de migration gerados
│   ├── env.py             # Configuração do Alembic
│   └── script.py.mako     # Template para novas migrations
├── app/
│   ├── core/
│   │   ├── config.py      # Settings via pydantic-settings
│   │   ├── database.py    # Engine async + fábrica de sessões
│   │   ├── security.py    # JWT + bcrypt helpers
│   │   └── deps.py        # Dependências FastAPI (get_db, get_current_user)
│   ├── models/            # Modelos SQLAlchemy ORM
│   ├── schemas/           # Schemas Pydantic v2 (request/response)
│   ├── routers/           # Rotas FastAPI por módulo
│   ├── services/          # Lógica de negócio pura
│   │   └── lottery_engine.py  ← KERNEL PRINCIPAL DO SORTEIO
│   ├── jobs/
│   │   └── scheduler.py   # APScheduler com lifespan
│   ├── utils/
│   │   ├── document_validator.py  # Validação CPF/CNPJ (algoritmo oficial)
│   │   └── business_days.py       # Cálculo de próximo dia útil
│   └── main.py            # Entrada da aplicação
├── seed.py                # Dados iniciais
├── alembic.ini
├── .env.example
├── requirements.txt
└── README.md
```

---

## 8. Papéis (Roles) e Permissões

| Role | Descrição | Permissões Principais |
|------|-----------|----------------------|
| `TI` | Administrador | Acesso total ao sistema |
| `JUDGE` | Juiz titular | Ver seus processos, recusar, reabrir |
| `ASSESSOR` | Assessor do juiz | Ver processos do juiz vinculado, editar pós-sorteio |
| `ASSISTANT` | Assistente | Cadastrar e editar processos (só pré-sorteio) |
| `TEMP_JUDGE` | Juiz temporário | Acesso restrito a UM processo específico |

---

## 9. Algoritmo de Sorteio (Resumo)

1. **Carga de dados**: processo, juízes ativos, estado global (LotteryState)
2. **Atalho REOPENED**: processo reaberto vai direto para o juiz original
3. **Filtragem de elegíveis**:
   - Remove juízes com conflito pré-cadastrado com a Person do processo
   - Para COMPLEX: aplica rodízio (remove quem já participou na rodada atual)
   - Verifica prioridade ("sorteio certeiro" pós-recusa)
4. **Seleção**: prioritária ou aleatória (`random.choice`)
5. **Atribuição**: atualiza processo, LotteryState e histórico (LotteryRound)
6. **Alerta de balanceamento**: avisa se diferença entre max/min de pesos > 3

---

## 10. Notas de Produção

- Troque `SECRET_KEY` por uma chave aleatória forte (ex: `openssl rand -hex 32`)
- Configure `ENVIRONMENT=production` para desativar logs SQL
- Restrinja o CORS em `app/main.py` para os domínios do front-end
- Use HTTPS em produção (configure no proxy reverso: nginx/caddy)
- Faça backup regular do banco e da pasta `uploads/`

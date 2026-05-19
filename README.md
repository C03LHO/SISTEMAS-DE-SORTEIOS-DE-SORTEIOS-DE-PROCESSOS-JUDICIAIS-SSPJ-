# Sistema de Sorteio e Distribuição de Processos Judiciais (SSPJ)

Sistema acadêmico para sortear automaticamente processos judiciais entre 8 juízes.

## 1. Instalação

```bash
pip install -r requirements.txt
```

## 2. Popular banco com dados de demonstração

```bash
python seed.py
```

Isso recria `sorteio.db` zerado com os usuários e processos de exemplo.

## 3. Subir o servidor

```bash
uvicorn main:app --reload
```

## 4. Abrir no navegador

- Front-end: <http://localhost:8000/>
- Swagger (API): <http://localhost:8000/docs>

## 5. Credenciais criadas pelo seed

| Perfil      | Login                        | Senha           |
|-------------|------------------------------|-----------------|
| TI          | `ti`                         | `ti123`         |
| Juiz 1..8   | `juiz1`..`juiz8`             | `juiz123`       |
| Assessor    | `assessor1`..`assessor8`     | `assessor123`   |
| Assistente  | `assistente1`, `assistente2` | `assistente123` |

## 6. Rodar os testes

```bash
pytest
```

12 testes (7 do algoritmo de sorteio + 5 de permissões), todos passando.

## 7. Tabela de permissões por perfil

| Recurso                          | TI | JUIZ | ASSESSOR | ASSISTENTE | JUIZ_EXT |
|----------------------------------|----|------|----------|------------|----------|
| Gerenciar usuários               | ✔  | —    | —        | —          | —        |
| Cadastrar pessoa                 | ✔  | —    | —        | ✔          | —        |
| Listar pessoas                   | ✔  | ✔    | ✔        | ✔          | —        |
| Cadastrar processo               | —  | —    | —        | ✔          | —        |
| Editar processo PENDENTE         | —  | —    | —        | ✔ (próprio)| —        |
| Editar processo SORTEADO         | —  | —    | ✔ (c/ autorização) | — | —     |
| Ver todos os processos           | ✔  | ✔    | só do juiz | só seus (mascarado) | só o designado |
| Executar sorteio manual          | ✔  | —    | —        | —          | —        |
| Ver logs de sorteio              | ✔  | ✔    | —        | —          | —        |
| Registrar conflito               | —  | ✔    | —        | —          | —        |
| Listar conflitos                 | ✔  | ✔    | —        | —          | —        |
| Designar juiz externo            | ✔  | —    | —        | —          | —        |
| Autorizar edição (assessor)      | —  | ✔    | —        | —          | —        |
| Marcar reabertura                | ✔  | ✔    | —        | —          | —        |

## 8. Fluxo do algoritmo de sorteio

Para cada processo PENDENTE (em ordem de cadastro):

```
1. Reaberto? → vai direto pro juiz_anterior (se ativo)

2. Tira da lista os juízes com conflito registrado
   Se sobrar zero → status = AGUARDANDO_JUIZ_EXTERNO

3. Se nível 3 (complexo):
   - remove o último juiz que recebeu complexo
   - mantém só quem ainda não recebeu na rodada atual
   - quando os 8 receberem, rodada reseta

4. Existe prioridade de compensação (mesmo nível,
   não consumida, juiz elegível)? → atribui ao mais antigo
   e marca a prioridade como consumida

5. Senão: random.choice entre os elegíveis

→ log_sorteio, status = SORTEADO, sorteado_em = now()
```

Tudo dentro de uma única transação. APScheduler roda diariamente
às 10h em dias úteis (timezone `America/Belem`), ignorando feriados
nacionais brasileiros.

## 9. Demonstração passo a passo (cada perfil)

> Antes: `python seed.py` e `uvicorn main:app --reload`, abra
> <http://localhost:8000/>.

### a) Como **TI** — `ti` / `ti123`
1. Em **Dashboard** veja os totais.
2. Vá em **Sorteio** → **"Executar sorteio agora"**. Os 10 processos
   PENDENTES são distribuídos. Os logs aparecem abaixo.
3. Em **Processos**, filtre por status e nível para conferir a distribuição.
4. Em **Usuários** crie/desative usuários.

### b) Como **Juiz** — `juiz1` / `juiz123`
1. **Meus Processos** — vê os atribuídos a ele.
2. Clique **"Marcar reabertura"** num processo. Faça login como TI
   e execute o sorteio: o processo volta direto para `juiz1`.
3. **Registrar Conflito**: selecione um processo seu, escreva a
   justificativa, anexe um arquivo qualquer. O processo volta para
   PENDENTE e uma prioridade de compensação fica registrada para o juiz.

### c) Como **Assessor** — `assessor1` / `assessor123`
1. **Processos do Meu Juiz** — só vê os de `juiz1`.
2. Clique **Editar** sem autorização → 403.
3. Volte como `juiz1`, use **"Autorizar edição"** no processo.
4. Como `assessor1`, edite o processo (token de uso único; nova edição
   exige nova autorização).

### d) Como **Assistente** — `assistente1` / `assistente123`
1. **Cadastrar Pessoa** (PF ou CNPJ).
2. **Cadastrar Processo** (número, descrição, nível 1/2/3, pessoa).
3. **Meus Cadastros** — só vê os que ele cadastrou, sem juiz/status real
   (mostra "cadastrado" ou "em processamento").

### e) Designar juiz externo (TI)
1. Como diferentes juízes, registre conflito num mesmo processo até
   esgotar os 8.
2. Execute o sorteio como TI → o processo fica `AGUARDANDO_JUIZ_EXTERNO`.
3. Em **Processos**, filtre por esse status e clique **"Designar externo"**.
   Informe login/senha/nome do juiz externo.

### f) Como **Juiz Externo** (login criado acima)
1. Loga e vê só **Meu Processo** — apenas o que lhe foi designado.

## Stack

FastAPI · SQLAlchemy 2 · SQLite · Pydantic v2 · JWT (python-jose + passlib) ·
APScheduler · pytest · Bootstrap 5 (CDN) · JS vanilla.

"""Gera um PDF didatico explicando o sistema."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    Preformatted,
)
from reportlab.lib.enums import TA_JUSTIFY

styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=18,
                    textColor=colors.HexColor("#0d3b66"), spaceAfter=12)
H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=14,
                    textColor=colors.HexColor("#0d3b66"), spaceAfter=8, spaceBefore=14)
H3 = ParagraphStyle("H3", parent=styles["Heading3"], fontSize=11,
                    textColor=colors.HexColor("#444"), spaceAfter=4, spaceBefore=8)
P = ParagraphStyle("P", parent=styles["BodyText"], fontSize=10.5, leading=14,
                   alignment=TA_JUSTIFY, spaceAfter=6)
LI = ParagraphStyle("LI", parent=P, leftIndent=14, bulletIndent=0)
CODE = ParagraphStyle("CODE", parent=styles["Code"], fontSize=8.5, leading=10.5,
                      textColor=colors.HexColor("#222"),
                      backColor=colors.HexColor("#f4f4f4"),
                      borderColor=colors.HexColor("#ccc"), borderWidth=0.5,
                      borderPadding=4, leftIndent=4, rightIndent=4)
NOTE = ParagraphStyle("NOTE", parent=P, backColor=colors.HexColor("#fff4ce"),
                      borderColor=colors.HexColor("#e3c441"), borderWidth=0.5,
                      borderPadding=6, leftIndent=4, rightIndent=4)


def p(t): return Paragraph(t, P)
def code(t): return Preformatted(t, CODE)
def note(t): return Paragraph(t, NOTE)


def tabela(cabec, linhas, larguras=None):
    dados = [cabec] + linhas
    t = Table(dados, colWidths=larguras, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d3b66")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#aaa")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f5f8fb")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def main():
    story = []

    # CAPA
    story += [
        Spacer(1, 4 * cm),
        Paragraph("Sistema de Sorteio e Distribuição de "
                  "Processos Judiciais", H1),
        Spacer(1, 0.4 * cm),
        Paragraph("Documentação técnica e didática do projeto",
                  ParagraphStyle("sub", parent=P, fontSize=13,
                                 textColor=colors.HexColor("#555"))),
        Spacer(1, 1.5 * cm),
        Paragraph("Este documento explica, parte por parte, como o sistema "
                  "funciona, qual a função de cada arquivo, qual a lógica "
                  "por trás das decisões e como demonstrar cada um dos "
                  "perfis de usuário.", P),
        Spacer(1, 2 * cm),
        Paragraph("Stack utilizada", H3),
        p("Back-end: Python 3.11+, FastAPI, SQLAlchemy 2, SQLite, "
          "Pydantic v2, JWT (python-jose + passlib), APScheduler, pytest."),
        p("Front-end: HTML5, JavaScript puro (sem framework), "
          "Bootstrap 5 via CDN, Bootstrap Icons, fetch API, localStorage."),
        PageBreak(),
    ]

    # 1. VISAO GERAL
    story += [
        Paragraph("1. Visão geral do sistema", H1),
        p("O sistema simula a rotina de um tribunal pequeno: um "
          "<b>assistente</b> cadastra processos, o sistema <b>sorteia</b> "
          "esses processos entre 8 <b>juízes</b>, e o <b>assessor</b> de "
          "cada juiz pode editar os processos sob autorização. O perfil "
          "<b>TI</b> administra o sistema todo, e o <b>juiz externo</b> "
          "é criado sob demanda quando os 8 juízes internos têm conflito "
          "com o mesmo processo."),
        Paragraph("1.1 Perfis de usuário e o que cada um faz", H2),
        tabela(
            ["Perfil", "Função no sistema"],
            [
                ["TI", "Administra tudo: usuários, sorteio manual, "
                       "designação de juiz externo, listagem geral."],
                ["JUIZ", "Vê seus processos, registra conflito de "
                         "interesse, autoriza o assessor a editar, marca "
                         "reabertura."],
                ["ASSESSOR", "Vê os processos do juiz ao qual está "
                             "vinculado e edita quando o juiz autoriza."],
                ["ASSISTENTE", "Cadastra pessoas (PF/PJ) e processos. "
                               "Não enxerga juiz nem status real."],
                ["JUIZ_EXTERNO", "Vê só o processo específico que o TI "
                                 "designou para ele."],
            ],
            larguras=[3 * cm, 13 * cm],
        ),
        Paragraph("1.2 O que é um processo aqui", H2),
        p("Um <b>processo</b> tem um número único, descrição, "
          "uma <b>pessoa</b> ligada (autor ou réu, PF ou PJ), e um "
          "<b>nível</b> de complexidade:"),
        Paragraph("• <b>Nível 1 (Básico)</b>: pode se repetir no mesmo "
                  "juiz à vontade.", LI),
        Paragraph("• <b>Nível 2 (Intermediário)</b>: pode se repetir "
                  "também.", LI),
        Paragraph("• <b>Nível 3 (Complexo)</b>: tem <b>rodízio</b>. Os "
                  "8 juízes recebem um cada antes que algum receba o "
                  "segundo, e ninguém pega dois complexos em sequência.", LI),
        Paragraph("1.3 Status que um processo pode ter", H2),
        tabela(
            ["Status", "Significado"],
            [
                ["PENDENTE", "Cadastrado mas ainda não sorteado."],
                ["SORTEADO", "Já tem juiz responsável."],
                ["AGUARDANDO_JUIZ_EXTERNO",
                 "Todos os 8 juízes têm conflito; o TI precisa designar "
                 "um juiz externo."],
                ["ENCERRADO", "Reservado para uso futuro."],
            ],
            larguras=[5 * cm, 11 * cm],
        ),
        PageBreak(),
    ]

    # 2. ESTRUTURA
    story += [
        Paragraph("2. Estrutura de pastas", H1),
        p("A organização do projeto é simples e plana — cada arquivo "
          "tem um papel claro:"),
        code("""sistema_sorteio/
├── main.py              # liga tudo: FastAPI, rotas, frontend, scheduler
├── database.py          # conexão com o SQLite
├── models.py            # tabelas do banco
├── schemas.py           # validação dos dados de entrada/saída (Pydantic)
├── auth.py              # senha, JWT, controle de perfil
├── sorteio.py           # o algoritmo do sorteio
├── scheduler.py         # roda o sorteio todo dia útil às 10h
├── seed.py              # popula o banco com usuários e exemplos
├── routers/             # endpoints separados por assunto
│   ├── usuarios.py
│   ├── pessoas.py
│   ├── processos.py
│   ├── sorteio_router.py
│   └── conflitos.py
├── frontend/
│   ├── login.html       # tela de login
│   ├── app.html         # aplicação principal (tudo numa página só)
│   ├── css/style.css    # ajustes visuais mínimos
│   └── js/
│       ├── api.js       # função wrapper que chama a API com o token
│       └── app.js       # lógica de telas, formulários, listas
├── tests/               # 12 testes automatizados
├── requirements.txt
└── README.md"""),
        note("<b>Por que essa estrutura?</b> Cada pasta agrupa um tipo "
             "de coisa. Quem mexe na regra do sorteio abre "
             "<i>sorteio.py</i>. Quem quer mudar a tela de login, "
             "<i>frontend/login.html</i>. Não há mistura."),
        PageBreak(),
    ]

    # 3. BANCO
    story += [
        Paragraph("3. O banco de dados", H1),
        p("Usamos <b>SQLite</b> — um banco em arquivo único "
          "(<i>sorteio.db</i>). Não precisa instalar servidor, não "
          "precisa configurar. Ideal para o trabalho acadêmico."),
        Paragraph("3.1 database.py — a conexão", H2),
        p("Esse arquivo só faz três coisas:"),
        Paragraph("• Cria a <b>engine</b> apontando para o arquivo "
                  "<i>sorteio.db</i>.", LI),
        Paragraph("• Cria a <b>SessionLocal</b>, que é como uma "
                  "&quot;sessão&quot; de conversa com o banco.", LI),
        Paragraph("• Define a função <b>get_db()</b> que abre e fecha "
                  "uma sessão automaticamente em cada requisição.", LI),
        code("""engine = create_engine("sqlite:///./sorteio.db", ...)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()"""),
        p("O <i>yield</i> em vez de <i>return</i> é o que permite o "
          "FastAPI &quot;injetar&quot; essa sessão dentro de cada "
          "endpoint, e ainda assim fechar a conexão depois — mesmo se "
          "der erro."),

        Paragraph("3.2 models.py — as tabelas", H2),
        p("Cada classe vira uma tabela. Resumo:"),
        tabela(
            ["Tabela", "O que guarda"],
            [
                ["usuarios", "Login, senha (hash), nome, perfil, ativo."],
                ["juizes", "Liga um usuário ao papel de juiz; tem tipo "
                          "PRINCIPAL ou EXTERNO."],
                ["assessores", "Liga um usuário a um juiz específico."],
                ["pessoas", "PF (CPF) ou PJ (CNPJ) que aparece nos "
                            "processos."],
                ["processos", "O processo em si: número, descrição, "
                              "nível, pessoa, status, juiz."],
                ["conflitos_interesse",
                 "Quando um juiz declara que não pode julgar um processo."],
                ["prioridades_compensacao",
                 "Marca que um juiz &quot;ficou devendo&quot; um processo "
                 "depois de declarar conflito."],
                ["acesso_juiz_externo",
                 "Quais processos cada juiz externo pode ver."],
                ["log_sorteio",
                 "Histórico de todo sorteio: data, processo, juiz, motivo."],
                ["autorizacoes_edicao",
                 "Tokens que o juiz dá ao assessor para editar um "
                 "processo (uso único)."],
            ],
            larguras=[5 * cm, 11 * cm],
        ),
        note("<b>Por que tabelas separadas para juízes e assessores se "
             "eles já têm uma linha em <i>usuarios</i>?</b> Para guardar "
             "informações que só fazem sentido para esse papel — por "
             "exemplo, qual juiz um assessor atende, ou se um juiz é "
             "principal ou externo. É a separação entre <i>quem você é</i> "
             "(usuário) e <i>qual seu papel</i> (juiz/assessor)."),
        PageBreak(),
    ]

    # 4. AUTH
    story += [
        Paragraph("4. Autenticação (auth.py)", H1),
        p("Quando o usuário faz login, devolvemos um <b>token JWT</b>. "
          "Esse token é uma string que o front-end guarda no "
          "<i>localStorage</i> e envia em todo pedido seguinte no "
          "cabeçalho <i>Authorization</i>."),
        Paragraph("4.1 Senha", H2),
        p("Nunca guardamos a senha em texto. Quando o usuário é criado, "
          "passamos a senha pelo <b>bcrypt</b> (via passlib), que "
          "devolve um hash. No login, comparamos a senha digitada com o "
          "hash."),
        code("""def hash_senha(s): return pwd_ctx.hash(s)
def verificar_senha(s, h): return pwd_ctx.verify(s, h)"""),
        Paragraph("4.2 Token JWT", H2),
        p("O token leva dentro dele o ID do usuário e uma data de "
          "expiração (12 horas). Tudo isso é assinado com uma chave "
          "secreta, então o servidor consegue confirmar que o token "
          "veio dele mesmo e não foi forjado."),
        code("""def criar_token(usuario_id):
    payload = {"sub": str(usuario_id),
               "exp": datetime.utcnow() + timedelta(minutes=720)}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")"""),
        Paragraph("4.3 Controle de perfil", H2),
        p("Cada endpoint usa uma <b>dependência</b> que pega o token, "
          "descobre o usuário e checa o perfil. Se o perfil não bater "
          "com o que aquele endpoint exige, devolve erro <b>403</b>."),
        code("""def exige_perfil(*perfis):
    def dep(u = Depends(usuario_atual)):
        if u.perfil not in perfis:
            raise HTTPException(403, "Acesso negado")
        return u
    return dep

# uso:
@router.post("/usuarios/")
def criar(..., _ = Depends(exige_perfil(PerfilEnum.TI))):
    ..."""),
        note("<b>Por que usar JWT em vez de sessão tradicional?</b> "
             "Como o front-end é estático (HTML+JS), não temos um "
             "&quot;estado de sessão&quot; no servidor. O JWT é "
             "auto-suficiente: o cliente o guarda, manda em cada "
             "request, e o servidor valida sem precisar consultar nada."),
        PageBreak(),
    ]

    # 5. SORTEIO
    story += [
        Paragraph("5. O coração do sistema: o algoritmo de sorteio", H1),
        p("O arquivo <b>sorteio.py</b> tem a função "
          "<b>executar_sorteio(db)</b>. Ela percorre todos os processos "
          "que estão no status PENDENTE, em ordem de cadastro, e tenta "
          "atribuir cada um a um juiz seguindo cinco etapas em cascata."),
        Paragraph("5.1 As cinco etapas, em linguagem simples", H2),
        Paragraph("<b>Etapa 1 — Reabertura:</b> se o processo foi "
                  "reaberto e tem um juiz anterior ativo, ele volta "
                  "direto pra esse juiz. Não cai no sorteio. A "
                  "ideia é manter o mesmo juiz para garantir "
                  "continuidade.", LI),
        Paragraph("<b>Etapa 2 — Conflito:</b> tiramos da lista qualquer "
                  "juiz que tenha declarado conflito de interesse "
                  "naquele processo. Se sobrar zero juiz, o processo "
                  "vai para AGUARDANDO_JUIZ_EXTERNO e o TI designa "
                  "alguém de fora.", LI),
        Paragraph("<b>Etapa 3 — Rodízio dos complexos (só nível 3):</b> "
                  "para evitar sobrecarregar um juiz, processos complexos "
                  "seguem duas regras: (a) não vai pro último juiz que "
                  "pegou um complexo, e (b) precisa ser alguém que ainda "
                  "não pegou complexo nessa &quot;rodada&quot;. Quando os "
                  "8 juízes pegaram um, a rodada zera.", LI),
        Paragraph("<b>Etapa 4 — Compensação:</b> se algum juiz declarou "
                  "conflito num processo desse mesmo nível antes, ele "
                  "tem prioridade agora — recebe o processo "
                  "automaticamente. Isso compensa a injustiça de ele ter "
                  "perdido um caso anterior.", LI),
        Paragraph("<b>Etapa 5 — Sorteio aleatório:</b> se nenhuma das "
                  "regras acima decidiu, escolhemos um juiz com "
                  "<i>random.choice()</i> entre os elegíveis.", LI),
        Paragraph("5.2 Por que tudo numa transação só?", H2),
        p("Se uma das etapas falhar no meio do processo, queremos "
          "<b>desfazer tudo</b> — não pode ficar metade dos processos "
          "sorteados e a outra metade não. Por isso colocamos toda a "
          "função num <i>try/except</i>: se der erro, <i>db.rollback()</i> "
          "desfaz; se chegar até o fim, <i>db.commit()</i> grava."),
        Paragraph("5.3 Por que precisamos do db.flush() dentro do loop?", H2),
        p("O SQLAlchemy, por padrão nas nossas configurações, não envia "
          "os <i>INSERT</i>s para o banco antes do commit. Como dentro "
          "do loop perguntamos &quot;qual foi o último juiz que pegou um "
          "complexo?&quot; — precisamos que o log da iteração anterior "
          "já esteja visível na consulta. O <i>flush()</i> empurra os "
          "dados pendentes para o banco sem fechar a transação."),
        note("Esse foi exatamente o bug que apareceu nos testes na "
             "primeira execução: o teste do rodízio achava só 5 juízes "
             "distintos em vez de 8. A correção foi colocar "
             "<i>db.flush()</i> depois de adicionar cada log."),
        PageBreak(),
    ]

    # 5.4 Tabela motivos
    story += [
        Paragraph("5.4 Cada sorteio gera um log", H2),
        p("Toda atribuição de juiz vira uma linha em <i>log_sorteio</i>. "
          "Isso serve de auditoria — qualquer pessoa consegue conferir "
          "depois o motivo de cada distribuição."),
        tabela(
            ["Motivo", "Quando acontece"],
            [
                ["SORTEIO_NORMAL", "Sorteio aleatório (caso comum)."],
                ["REABERTURA", "Processo voltou pro juiz anterior."],
                ["PRIORIDADE_COMPENSACAO",
                 "Juiz tinha ficado devendo um processo desse nível."],
                ["DESIGNACAO_EXTERNA",
                 "TI designou um juiz de fora manualmente."],
            ],
            larguras=[5.5 * cm, 10.5 * cm],
        ),
        Paragraph("5.5 Quando o sorteio roda automaticamente", H2),
        p("O arquivo <b>scheduler.py</b> usa a biblioteca "
          "<b>APScheduler</b> para agendar o sorteio às <b>10:00 da "
          "manhã</b>, no fuso de Belém, <b>todo dia útil</b>. A "
          "biblioteca <i>holidays</i> nos diz se a data é feriado "
          "nacional. Em sábado, domingo ou feriado o job simplesmente "
          "não faz nada."),
        code("""sched.add_job(_job, CronTrigger(hour=10, minute=0,
                                  timezone="America/Belem"))"""),
        p("O TI também pode disparar o sorteio na hora pelo botão "
          "&quot;Executar sorteio agora&quot;, que chama o endpoint "
          "<i>POST /sorteio/executar</i>."),
        PageBreak(),
    ]

    # 6. ROTAS
    story += [
        Paragraph("6. Os endpoints da API", H1),
        p("Cada router cuida de uma área. O FastAPI gera "
          "automaticamente o <b>/docs</b> (Swagger) onde você pode "
          "testar cada endpoint sem precisar do front-end."),
        Paragraph("6.1 /auth/login", H2),
        p("Recebe <i>login</i> e <i>senha</i>. Se baterem, devolve um "
          "JSON com <i>token</i>, perfil, nome, e os IDs auxiliares "
          "(juiz_id ou assessor_id quando aplicável)."),
        Paragraph("6.2 /usuarios/* — só TI", H2),
        p("CRUD de usuários. O TI cria juízes, assessores, "
          "assistentes. Quando cria um juiz, automaticamente também "
          "cria o registro em <i>juizes</i>."),
        Paragraph("6.3 /pessoas/*", H2),
        p("Assistente e TI cadastram pessoas (PF/PJ). Os outros perfis "
          "só listam. A validação básica do tamanho do CPF (11 dígitos) "
          "e do CNPJ (14 dígitos) acontece tanto no back quanto no front."),
        Paragraph("6.4 /processos/*", H2),
        p("Aqui mora a maior parte da lógica de permissão. Resumo:"),
        tabela(
            ["Ação", "Quem pode"],
            [
                ["Criar processo", "Só ASSISTENTE."],
                ["Editar (PENDENTE)",
                 "Só o ASSISTENTE que criou."],
                ["Editar (SORTEADO)",
                 "Só o ASSESSOR do juiz, com autorização."],
                ["Listar", "Cada perfil vê uma fatia diferente."],
                ["Marcar reabertura", "TI ou JUIZ."],
                ["Autorizar edição", "Só o JUIZ responsável."],
            ],
            larguras=[5 * cm, 11 * cm],
        ),
        p("Na hora de listar, fizemos uma função <i>serializar</i> que "
          "monta o JSON. Para o assistente, esse JSON é diferente: "
          "escondemos <i>juiz_id</i>, <i>sorteado_em</i> e mostramos um "
          "status genérico (&quot;cadastrado&quot; ou &quot;em "
          "processamento&quot;). Isso garante que ele não fica sabendo "
          "qual juiz pegou o processo dele."),
        Paragraph("6.5 /conflitos/*", H2),
        p("Quando um <b>juiz</b> envia um conflito, três coisas "
          "acontecem ao mesmo tempo: (1) registra o conflito com o "
          "arquivo anexado; (2) cria uma prioridade de compensação para "
          "ele; (3) o processo volta para PENDENTE. No próximo sorteio, "
          "aquele juiz não aparece como elegível para esse processo, "
          "mas tem prioridade no próximo processo do mesmo nível."),
        p("Quando o <b>TI</b> designa um juiz externo, criamos no "
          "mesmo movimento: o usuário (perfil JUIZ_EXTERNO), o juiz "
          "(tipo EXTERNO), o registro em <i>acesso_juiz_externo</i> e "
          "o log do sorteio com motivo DESIGNACAO_EXTERNA."),
        Paragraph("6.6 /sorteio/*", H2),
        p("Dois endpoints: <i>POST /sorteio/executar</i> roda o "
          "algoritmo (só TI); <i>GET /sorteio/logs</i> lista o "
          "histórico (TI ou JUIZ)."),
        PageBreak(),
    ]

    # 7. FRONTEND
    story += [
        Paragraph("7. O front-end", H1),
        p("Tudo em <b>HTML + JavaScript puro</b>, sem build, sem "
          "framework. O FastAPI serve os arquivos estáticos da pasta "
          "<i>frontend/</i>."),
        Paragraph("7.1 Duas páginas só", H2),
        Paragraph("• <b>login.html</b>: formulário pequeno; ao "
                  "enviar, chama <i>POST /auth/login</i>, guarda o "
                  "retorno no <i>localStorage</i> e redireciona para "
                  "/app.", LI),
        Paragraph("• <b>app.html</b>: uma única página com várias "
                  "<i>&lt;section&gt;</i>, cada uma é uma &quot;tela&quot;. "
                  "O JavaScript esconde todas e mostra só a que está "
                  "ativa. É uma SPA caseira.", LI),
        Paragraph("7.2 api.js — o wrapper que fala com o servidor", H2),
        p("Essa função é a única que faz <i>fetch()</i> no projeto. "
          "Ela sempre coloca o token no cabeçalho, sabe quando os "
          "dados são JSON e quando são FormData (para upload de "
          "arquivo), e se receber 401 já desloga e manda pra tela de "
          "login."),
        code("""async function api(path, opts = {}) {
  const auth = getAuth();
  const headers = opts.headers || {};
  if (auth?.token) headers['Authorization'] = `Bearer ${auth.token}`;
  // se for um objeto JS comum, converte pra JSON
  if (!(opts.body instanceof FormData) && opts.body
      && typeof opts.body !== 'string') {
    headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(opts.body);
  }
  const r = await fetch(API_BASE + path, { ...opts, headers });
  if (r.status === 401) {
    clearAuth();
    window.location.href = '/';
    return;
  }
  ...
}"""),
        Paragraph("7.3 app.js — a lógica das telas", H2),
        p("Esse arquivo tem três partes principais:"),
        Paragraph("• Um <b>dicionário MENUS</b> que diz quais opções "
                  "cada perfil vê na sidebar. Assim, o menu de "
                  "&quot;Sorteio&quot; só aparece para TI, e "
                  "&quot;Cadastrar Processo&quot; só para o assistente.", LI),
        Paragraph("• A função <b>mostrarTela(id)</b>, que esconde "
                  "todas as <i>&lt;section&gt;</i> e mostra só uma. "
                  "Depois chama <b>carregarTela(id)</b> que busca os "
                  "dados da API para popular a tabela ou form.", LI),
        Paragraph("• Os <b>handlers</b> dos formulários (login do "
                  "usuário, cadastro de pessoa, cadastro de processo, "
                  "executar sorteio, registrar conflito, etc.), que "
                  "chamam <i>api()</i> e mostram um alerta de sucesso "
                  "ou erro em cima da tela.", LI),
        note("<b>Por que não usar React/Vue?</b> O escopo é pequeno e "
             "o objetivo do trabalho é mostrar as regras do sorteio, "
             "não a arquitetura do front. JS puro funciona muito bem "
             "aqui e tira a complexidade de build, dependências, etc."),
        PageBreak(),
    ]

    # 8. SEED
    story += [
        Paragraph("8. Dados de demonstração (seed.py)", H1),
        p("Para não precisar criar cada usuário e processo na mão, o "
          "<b>seed.py</b> zera o banco e popula com:"),
        tabela(
            ["Quantidade", "O quê", "Login / senha"],
            [
                ["1", "TI", "ti / ti123"],
                ["8", "Juízes principais",
                 "juiz1..juiz8 / juiz123"],
                ["8", "Assessores (um por juiz)",
                 "assessor1..assessor8 / assessor123"],
                ["2", "Assistentes",
                 "assistente1..2 / assistente123"],
                ["5", "Pessoas (3 PF + 2 PJ)", "—"],
                ["10", "Processos PENDENTES misturando "
                       "níveis 1, 2 e 3", "—"],
            ],
            larguras=[2.5 * cm, 8 * cm, 5.5 * cm],
        ),
        p("Rodar com: <i>python seed.py</i>"),
        PageBreak(),
    ]

    # 9. TESTES
    story += [
        Paragraph("9. Os testes automatizados", H1),
        p("São <b>12 testes</b>, organizados em dois arquivos. "
          "Todos passam. Para rodá-los: <i>pytest</i>"),
        Paragraph("9.1 tests/test_sorteio.py — 7 testes da regra", H2),
        Paragraph("• <b>Reabertura</b>: processo reaberto volta para o "
                  "juiz anterior, sem cair no sorteio.", LI),
        Paragraph("• <b>Não-consecutividade</b>: dois complexos "
                  "seguidos não vão para o mesmo juiz.", LI),
        Paragraph("• <b>Rodízio completo</b>: 8 processos complexos "
                  "→ exatamente 1 para cada juiz.", LI),
        Paragraph("• <b>Conflito tira o juiz</b>: se 7 dos 8 juízes têm "
                  "conflito, o oitavo recebe o processo.", LI),
        Paragraph("• <b>Compensação</b>: o juiz que tinha prioridade "
                  "recebe o próximo do mesmo nível, e a prioridade fica "
                  "marcada como consumida.", LI),
        Paragraph("• <b>Conflito de todos</b>: o processo vai para "
                  "AGUARDANDO_JUIZ_EXTERNO.", LI),
        Paragraph("• <b>Níveis 1 e 2 podem repetir</b>: com 20 "
                  "processos básicos para 8 juízes, é normal que algum "
                  "receba mais de um.", LI),
        Paragraph("9.2 tests/test_permissoes.py — 5 testes de acesso", H2),
        Paragraph("• Assistente não vê o status real, nem o "
                  "<i>juiz_id</i>.", LI),
        Paragraph("• Assessor só vê processos do seu juiz.", LI),
        Paragraph("• Assessor não consegue editar sem autorização "
                  "(403).", LI),
        Paragraph("• Juiz externo só enxerga o processo que lhe foi "
                  "designado.", LI),
        Paragraph("• Juiz comum não consegue criar usuário "
                  "(403).", LI),
        note("Os testes usam SQLite em memória (não tocam o "
             "<i>sorteio.db</i> real) e o <i>TestClient</i> do FastAPI, "
             "que simula requisições HTTP sem subir servidor."),
        PageBreak(),
    ]

    # 10. RODAR
    story += [
        Paragraph("10. Como rodar e demonstrar", H1),
        Paragraph("10.1 Subir o sistema", H2),
        code("""pip install -r requirements.txt
python seed.py
uvicorn main:app --reload"""),
        p("Abrir <b>http://localhost:8000/</b>. A documentação "
          "interativa da API fica em <b>http://localhost:8000/docs</b>."),
        Paragraph("10.2 Roteiro de demonstração", H2),
        Paragraph("<b>1. Como TI</b> (ti / ti123)", H3),
        Paragraph("Login → Dashboard mostra os totais → vai em "
                  "&quot;Sorteio&quot; → clica &quot;Executar sorteio "
                  "agora&quot;. Os 10 processos PENDENTES são "
                  "distribuídos e aparecem na tabela de logs.", LI),
        Paragraph("<b>2. Como Juiz</b> (juiz1 / juiz123)", H3),
        Paragraph("Login → &quot;Meus Processos&quot;: vê os que "
                  "ganhou no sorteio. Pode usar &quot;Marcar "
                  "reabertura&quot; (e ao executar o sorteio de novo "
                  "como TI, o processo volta para juiz1).", LI),
        Paragraph("Em &quot;Registrar Conflito&quot;: escolhe um "
                  "processo, escreve a justificativa, anexa qualquer "
                  "arquivo. O processo volta para PENDENTE e uma "
                  "prioridade é registrada.", LI),
        Paragraph("<b>3. Como Assessor</b> (assessor1 / assessor123)", H3),
        Paragraph("Login → &quot;Processos do Meu Juiz&quot;: só vê os "
                  "do juiz1. Se clicar em &quot;Editar&quot; sem "
                  "autorização → erro 403.", LI),
        Paragraph("Voltar como juiz1 → &quot;Autorizar edição&quot; "
                  "naquele processo → voltar como assessor1 e editar. "
                  "Funciona uma vez só.", LI),
        Paragraph("<b>4. Como Assistente</b> (assistente1 / assistente123)", H3),
        Paragraph("Login → &quot;Cadastrar Pessoa&quot;, depois "
                  "&quot;Cadastrar Processo&quot;. Em &quot;Meus "
                  "Cadastros&quot; aparece só o que ele cadastrou, sem "
                  "mostrar juiz e com status genérico "
                  "(&quot;cadastrado&quot; ou &quot;em "
                  "processamento&quot;).", LI),
        Paragraph("<b>5. Cenário do juiz externo</b>", H3),
        Paragraph("Para forçar: como cada juiz, registrar conflito no "
                  "mesmo processo (precisa estar com aquele juiz "
                  "naquele momento). Quando os 8 conflitos forem "
                  "registrados e o sorteio rodar, o processo cai em "
                  "AGUARDANDO_JUIZ_EXTERNO. O TI vai em "
                  "&quot;Processos&quot;, filtra por esse status e "
                  "clica em &quot;Designar externo&quot;. Pronto — o "
                  "novo login do juiz externo entra no sistema e vê só "
                  "esse processo.", LI),
        PageBreak(),
    ]

    # 11. CONCLUSAO
    story += [
        Paragraph("11. Pontos importantes para a apresentação", H1),
        Paragraph("• <b>Separação por perfil</b>: a regra de quem pode "
                  "o quê está espalhada no back-end (dependências do "
                  "FastAPI), no banco (qual usuário é juiz/assessor) e "
                  "no front-end (sidebar montada conforme o perfil).", LI),
        Paragraph("• <b>Auditabilidade</b>: cada sorteio gera um log "
                  "permanente com data, juiz, processo e motivo. "
                  "Nunca se perde a história de como um processo "
                  "chegou a quem.", LI),
        Paragraph("• <b>Justiça do sorteio</b>: a combinação das "
                  "etapas (reabertura → conflito → rodízio → "
                  "compensação → sorteio) garante que ninguém é "
                  "sobrecarregado e que situações imprevistas "
                  "(conflito, reabertura) são tratadas de forma "
                  "previsível.", LI),
        Paragraph("• <b>Atomicidade</b>: todo o sorteio é uma só "
                  "transação. Se algo falhar no meio, nada é gravado. "
                  "Isso protege a integridade dos dados.", LI),
        Paragraph("• <b>Simplicidade do front-end</b>: tudo HTML/JS "
                  "puro. Para mostrar uma tela, basta dar um "
                  "<i>display: block</i> nela. Para falar com o "
                  "servidor, uma única função <i>api()</i> faz tudo.", LI),
        Paragraph("• <b>Testes garantem que as regras funcionam</b>: "
                  "12 testes cobrem o sorteio e as permissões. Rodar "
                  "<i>pytest</i> antes da apresentação dá segurança de "
                  "que nada quebrou.", LI),
        Spacer(1, 1 * cm),
        p("<b>Em uma frase:</b> O sistema é um servidor FastAPI que "
          "expõe uma API REST protegida por JWT, com regras de sorteio "
          "implementadas em uma função pura testável, persistência em "
          "SQLite, e uma interface web simples em Bootstrap que mostra "
          "para cada perfil exatamente o que ele precisa ver."),
    ]

    doc = SimpleDocTemplate(
        "Documentacao_SSPJ.pdf", pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title="Documentação SSPJ",
        author="Projeto SSPJ",
    )
    doc.build(story)
    print("PDF gerado: Documentacao_SSPJ.pdf")


if __name__ == "__main__":
    main()

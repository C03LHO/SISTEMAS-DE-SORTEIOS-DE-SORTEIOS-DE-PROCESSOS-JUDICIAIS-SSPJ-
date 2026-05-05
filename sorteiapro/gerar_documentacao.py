"""
Gerador de documentacao tecnica do SorteiaPro em PDF.
Executa com: python gerar_documentacao.py
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from reportlab.pdfgen import canvas as rl_canvas

# ─── Paleta de cores ──────────────────────────────────────────────────────────
AZUL_ESCURO   = colors.HexColor("#1a2e4a")
AZUL_MEDIO    = colors.HexColor("#2563eb")
AZUL_CLARO    = colors.HexColor("#dbeafe")
CINZA_ESCURO  = colors.HexColor("#1f2937")
CINZA_MEDIO   = colors.HexColor("#4b5563")
CINZA_CLARO   = colors.HexColor("#f3f4f6")
VERDE         = colors.HexColor("#16a34a")
VERDE_CLARO   = colors.HexColor("#dcfce7")
LARANJA       = colors.HexColor("#ea580c")
LARANJA_CLARO = colors.HexColor("#ffedd5")
ROXO          = colors.HexColor("#7c3aed")
ROXO_CLARO    = colors.HexColor("#ede9fe")
BRANCO        = colors.white

PAGE_W, PAGE_H = A4


# ─── Numeracao de paginas ─────────────────────────────────────────────────────
def add_page_number(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(CINZA_MEDIO)
    # Rodape esquerdo
    canvas_obj.drawString(2 * cm, 1.2 * cm, "SorteiaPro — Documentacao Tecnica")
    # Rodape direito
    page_num = f"Pagina {doc.page}"
    canvas_obj.drawRightString(PAGE_W - 2 * cm, 1.2 * cm, page_num)
    # Linha do rodape
    canvas_obj.setStrokeColor(AZUL_MEDIO)
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(2 * cm, 1.6 * cm, PAGE_W - 2 * cm, 1.6 * cm)
    canvas_obj.restoreState()


# ─── Estilos ──────────────────────────────────────────────────────────────────
def criar_estilos():
    base = getSampleStyleSheet()

    estilos = {}

    estilos["titulo_capa"] = ParagraphStyle(
        "titulo_capa",
        fontName="Helvetica-Bold",
        fontSize=28,
        textColor=BRANCO,
        alignment=TA_CENTER,
        spaceAfter=10,
    )
    estilos["subtitulo_capa"] = ParagraphStyle(
        "subtitulo_capa",
        fontName="Helvetica",
        fontSize=14,
        textColor=colors.HexColor("#bfdbfe"),
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    estilos["h1"] = ParagraphStyle(
        "h1",
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=AZUL_ESCURO,
        spaceBefore=18,
        spaceAfter=8,
        borderPad=4,
    )
    estilos["h2"] = ParagraphStyle(
        "h2",
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=AZUL_MEDIO,
        spaceBefore=14,
        spaceAfter=5,
    )
    estilos["h3"] = ParagraphStyle(
        "h3",
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=CINZA_ESCURO,
        spaceBefore=10,
        spaceAfter=4,
    )
    estilos["body"] = ParagraphStyle(
        "body",
        fontName="Helvetica",
        fontSize=9.5,
        textColor=CINZA_ESCURO,
        leading=15,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    )
    estilos["bullet"] = ParagraphStyle(
        "bullet",
        fontName="Helvetica",
        fontSize=9.5,
        textColor=CINZA_ESCURO,
        leading=14,
        leftIndent=14,
        spaceAfter=3,
    )
    estilos["code"] = ParagraphStyle(
        "code",
        fontName="Courier",
        fontSize=8,
        textColor=colors.HexColor("#1e3a5f"),
        backColor=CINZA_CLARO,
        leading=12,
        leftIndent=8,
        rightIndent=8,
        spaceAfter=2,
        spaceBefore=2,
    )
    estilos["code_destaque"] = ParagraphStyle(
        "code_destaque",
        fontName="Courier-Bold",
        fontSize=8.5,
        textColor=AZUL_ESCURO,
        leading=13,
        leftIndent=8,
    )
    estilos["nota"] = ParagraphStyle(
        "nota",
        fontName="Helvetica-Oblique",
        fontSize=9,
        textColor=colors.HexColor("#374151"),
        backColor=AZUL_CLARO,
        leftIndent=10,
        rightIndent=10,
        spaceAfter=6,
        spaceBefore=4,
        borderPad=6,
        leading=13,
    )
    estilos["aviso"] = ParagraphStyle(
        "aviso",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=colors.HexColor("#92400e"),
        backColor=LARANJA_CLARO,
        leftIndent=10,
        rightIndent=10,
        spaceAfter=6,
        spaceBefore=4,
        borderPad=6,
        leading=13,
    )
    estilos["label"] = ParagraphStyle(
        "label",
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=AZUL_MEDIO,
    )
    estilos["toc"] = ParagraphStyle(
        "toc",
        fontName="Helvetica",
        fontSize=10,
        textColor=CINZA_ESCURO,
        leading=16,
    )
    return estilos


# ─── Helpers visuais ──────────────────────────────────────────────────────────
def secao_colorida(titulo, cor_fundo, cor_texto, e):
    """Cabecalho colorido de secao."""
    return Table(
        [[Paragraph(titulo, ParagraphStyle(
            "sh", fontName="Helvetica-Bold", fontSize=12,
            textColor=cor_texto, alignment=TA_LEFT
        ))]],
        colWidths=[16.5 * cm],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), cor_fundo),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("ROUNDEDCORNERS", [4, 4, 4, 4]),
        ]),
    )


def caixa_codigo(linhas, e):
    """Bloco de codigo com fundo cinza."""
    itens = []
    for linha in linhas:
        itens.append(Paragraph(linha.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"),
                               e["code"]))
    return Table(
        [[item] for item in itens],
        colWidths=[16.5 * cm],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), CINZA_CLARO),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
            ("LINEAFTER", (0, 0), (0, -1), 3, AZUL_MEDIO),
        ]),
    )


def tabela_campos(colunas, dados, e, larguras=None):
    """Tabela de campos/valores."""
    if not larguras:
        larguras = [4 * cm, 12.5 * cm]

    header = [
        Paragraph(f"<b>{c}</b>", ParagraphStyle(
            "th", fontName="Helvetica-Bold", fontSize=9,
            textColor=BRANCO, alignment=TA_CENTER
        ))
        for c in colunas
    ]
    rows = [[Paragraph(str(c), ParagraphStyle(
        "td", fontName="Helvetica", fontSize=9, textColor=CINZA_ESCURO
    )) for c in row] for row in dados]

    table = Table(
        [header] + rows,
        colWidths=larguras,
        repeatRows=1,
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_ESCURO),
        ("BACKGROUND", (0, 1), (-1, -1), BRANCO),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BRANCO, CINZA_CLARO]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTRUCAO DO DOCUMENTO
# ═══════════════════════════════════════════════════════════════════════════════
def build_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2.0 * cm,
        leftMargin=2.0 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.4 * cm,
        title="SorteiaPro - Documentacao Tecnica Completa",
        author="SorteiaPro / TI Tribunal Regional",
    )

    e = criar_estilos()
    story = []

    # =========================================================================
    # CAPA
    # =========================================================================
    def capa(canvas_obj, doc_obj):
        canvas_obj.saveState()
        # Fundo azul escuro
        canvas_obj.setFillColor(AZUL_ESCURO)
        canvas_obj.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        # Faixa azul medio superior
        canvas_obj.setFillColor(AZUL_MEDIO)
        canvas_obj.rect(0, PAGE_H - 6 * cm, PAGE_W, 6 * cm, fill=1, stroke=0)
        # Faixa inferior
        canvas_obj.setFillColor(colors.HexColor("#0f172a"))
        canvas_obj.rect(0, 0, PAGE_W, 3.5 * cm, fill=1, stroke=0)
        # Titulo
        canvas_obj.setFont("Helvetica-Bold", 36)
        canvas_obj.setFillColor(BRANCO)
        canvas_obj.drawCentredString(PAGE_W / 2, PAGE_H - 4.2 * cm, "SorteiaPro")
        # Subtitulo
        canvas_obj.setFont("Helvetica", 15)
        canvas_obj.setFillColor(colors.HexColor("#bfdbfe"))
        canvas_obj.drawCentredString(PAGE_W / 2, PAGE_H - 5.1 * cm,
                                     "Documentacao Tecnica Completa do Codigo-Fonte")
        # Linha divisoria
        canvas_obj.setStrokeColor(AZUL_MEDIO)
        canvas_obj.setLineWidth(1.5)
        canvas_obj.line(3 * cm, PAGE_H / 2 + 2 * cm, PAGE_W - 3 * cm, PAGE_H / 2 + 2 * cm)
        # Descricao central
        canvas_obj.setFont("Helvetica", 11)
        canvas_obj.setFillColor(colors.HexColor("#93c5fd"))
        linhas_desc = [
            "Sistema Backend para Tribunal Regional",
            "Gerenciamento de Processos Judiciais com Sorteio Automatico de Juizes",
            "",
            "Stack: Python 3.12 | FastAPI | SQLAlchemy 2.0 | PostgreSQL",
            "APScheduler | JWT | Pydantic v2 | Alembic",
        ]
        y = PAGE_H / 2 + 1.0 * cm
        for linha in linhas_desc:
            canvas_obj.drawCentredString(PAGE_W / 2, y, linha)
            y -= 0.65 * cm
        # Rodape da capa
        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.setFillColor(colors.HexColor("#64748b"))
        canvas_obj.drawCentredString(PAGE_W / 2, 2.2 * cm,
                                     "Tribunal Regional — Setor de Tecnologia da Informacao")
        canvas_obj.drawCentredString(PAGE_W / 2, 1.6 * cm, "2025")
        canvas_obj.restoreState()

    # Pagina de capa separada (sem conteudo de story)
    story.append(Spacer(1, PAGE_H))  # placeholder — sera substituido

    # =========================================================================
    # SUMARIO
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("Sumario", e["h1"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=AZUL_MEDIO))
    story.append(Spacer(1, 0.3 * cm))

    sumario_itens = [
        ("1", "Visao Geral do Sistema", "Proposito, tecnologias e arquitetura"),
        ("2", "Estrutura de Pastas", "Organizacao completa do projeto"),
        ("3", "Configuracoes e Ambiente", "config.py, .env, variaveis de ambiente"),
        ("4", "Banco de Dados", "database.py — engine async e sessoes"),
        ("5", "Seguranca (JWT + bcrypt)", "security.py — tokens e hashes"),
        ("6", "Dependencias FastAPI", "deps.py — get_db, get_current_user, RBAC"),
        ("7", "Modelos SQLAlchemy", "Todas as tabelas do banco de dados"),
        ("8", "Schemas Pydantic v2", "Validacao de entrada e saida"),
        ("9", "Kernel de Sorteio", "lottery_engine.py — algoritmo completo (8 passos)"),
        ("10", "Servicos de Negocio", "user, process, conflict, audit services"),
        ("11", "Agendador (Scheduler)", "APScheduler + lifespan do FastAPI"),
        ("12", "Routers (Endpoints)", "Todas as rotas e suas permissoes"),
        ("13", "Utilitarios", "Validacao CPF/CNPJ e dias uteis"),
        ("14", "Seed Inicial", "Dados iniciais do sistema"),
        ("15", "Alembic (Migrations)", "Configuracao e geracao de migrations"),
        ("16", "Como Executar", "Passo a passo para rodar o sistema"),
        ("17", "Fluxos Principais", "Diagramas de fluxo em texto"),
        ("18", "Checklist de Regras", "Todas as regras de negocio implementadas"),
    ]

    for num, titulo, desc in sumario_itens:
        row = Table(
            [[
                Paragraph(f"<b>{num}.</b>", ParagraphStyle(
                    "sn", fontName="Helvetica-Bold", fontSize=10,
                    textColor=AZUL_MEDIO, alignment=TA_CENTER
                )),
                Paragraph(f"<b>{titulo}</b><br/>"
                          f"<font size='8' color='#6b7280'>{desc}</font>",
                          ParagraphStyle("st", fontName="Helvetica", fontSize=10,
                                         textColor=CINZA_ESCURO, leading=14)),
            ]],
            colWidths=[1.2 * cm, 15.3 * cm],
        )
        row.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(row)

    # =========================================================================
    # CAP 1 — VISAO GERAL
    # =========================================================================
    story.append(PageBreak())
    story.append(secao_colorida("1. Visao Geral do Sistema", AZUL_ESCURO, BRANCO, e))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        "O <b>SorteiaPro</b> e um sistema backend completo para um Tribunal Regional, "
        "responsavel por gerenciar processos judiciais e realizar o sorteio automatico "
        "de juizes de forma imparcial, rastreavel e auditavel. Todo o codigo e "
        "escrito em Python 3.12 e segue as melhores praticas de desenvolvimento moderno.",
        e["body"]
    ))

    story.append(Paragraph("Funcionalidades Principais", e["h2"]))
    funcionalidades = [
        ("Sorteio Automatico", "APScheduler dispara o sorteio toda segunda a sexta as 10:00 (horario de Brasilia). Cada processo com status PENDING_LOTTERY ou REOPENED e agendado para o proximo dia util as 10h."),
        ("Algoritmo de Rodizio", "Processos COMPLEX passam por rodizio obrigatorio: todos os 8 juizes devem receber um processo COMPLEX antes de qualquer um receber o segundo. BASIC e INTERMEDIATE nao tem restricao de rodizio."),
        ("Balanceamento de Carga", "O sistema soma pesos (BASIC=1, INTERMEDIATE=2, COMPLEX=3) por juiz. Se a diferenca entre o maximo e o minimo ultrapassar 3, um BALANCE_ALERT e gerado no AuditLog."),
        ("Sorteio Certeiro", "Quando um juiz recusa um processo, ele recebe prioridade no proximo sorteio do mesmo nivel — garantindo que a recusa nao o prejudique duplamente."),
        ("Conflito de Interesse", "Juizes com conflito pre-cadastrado com a Person do processo sao automaticamente removidos da lista de elegiveis. A recusa formal requer documento comprobatorio."),
        ("Juiz Temporario", "Quando todos os titulares recusam, o TI nomeia um juiz temporario (TEMP_JUDGE) com acesso restrito exclusivamente ao processo designado."),
        ("RBAC Completo", "5 roles: TI (admin), JUDGE, ASSESSOR, ASSISTANT, TEMP_JUDGE. Cada endpoint valida o role antes de processar a requisicao."),
        ("Auditoria Total", "Todas as acoes importantes sao gravadas no AuditLog de forma APPEND-ONLY — nenhuma entrada e modificada ou deletada."),
    ]
    for nome, desc in funcionalidades:
        story.append(Paragraph(f"<b>• {nome}:</b> {desc}", e["bullet"]))
        story.append(Spacer(1, 0.1 * cm))

    story.append(Paragraph("Stack Tecnologica", e["h2"]))
    story.append(tabela_campos(
        ["Tecnologia", "Versao / Descricao"],
        [
            ["Python", "3.12+ — linguagem principal"],
            ["FastAPI", "Framework web ASGI moderno e de alta performance"],
            ["SQLAlchemy", "2.0 — ORM com suporte a async (Mapped + mapped_column)"],
            ["asyncpg", "Driver async para PostgreSQL (mais rapido que psycopg2 async)"],
            ["Alembic", "Gerador de migrations — detecta mudancas nos modelos automaticamente"],
            ["psycopg2-binary", "Driver sincrono para o Alembic (migrations nao sao async)"],
            ["python-jose", "Criacao e validacao de tokens JWT (HS256)"],
            ["passlib[bcrypt]", "Hash seguro de senhas com bcrypt"],
            ["APScheduler 3.x", "BackgroundScheduler com CronTrigger para sorteios automaticos"],
            ["Pydantic v2", "Validacao de dados de entrada e saida (schemas)"],
            ["pydantic-settings", "Carregamento de variaveis de ambiente via .env"],
            ["python-multipart", "Suporte a upload de arquivos (multipart/form-data)"],
            ["Uvicorn", "Servidor ASGI de producao para rodar o FastAPI"],
        ],
        e,
        larguras=[4.5 * cm, 12 * cm],
    ))

    # =========================================================================
    # CAP 2 — ESTRUTURA DE PASTAS
    # =========================================================================
    story.append(PageBreak())
    story.append(secao_colorida("2. Estrutura de Pastas do Projeto", AZUL_ESCURO, BRANCO, e))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        "O projeto segue uma arquitetura em camadas bem definida. "
        "Cada pasta tem uma responsabilidade especifica, facilitando a manutencao "
        "e o entendimento do codigo.",
        e["body"]
    ))

    estrutura = [
        ("sorteiapro/", "Raiz do projeto"),
        ("  alembic/", "Configuracao e migrations do banco de dados"),
        ("    versions/", "Arquivos de migration gerados automaticamente"),
        ("    env.py", "Configuracao do Alembic (importa modelos, lê .env)"),
        ("  app/", "Codigo-fonte principal da aplicacao"),
        ("    core/", "Modulos fundamentais compartilhados por toda a app"),
        ("      config.py", "Variaveis de ambiente via pydantic-settings"),
        ("      database.py", "Engine async, sessoes e Base declarativa"),
        ("      security.py", "Funcoes JWT e bcrypt"),
        ("      deps.py", "Dependencias FastAPI (get_db, autenticacao, RBAC)"),
        ("    models/", "Modelos SQLAlchemy ORM — mapeiam tabelas do banco"),
        ("      user.py", "Tabela users + enum UserRole"),
        ("      person.py", "Tabela persons + enum DocumentType"),
        ("      process.py", "Tabela processes + enums ProcessLevel/Status"),
        ("      lottery.py", "Tabelas lottery_rounds e lottery_state (singleton)"),
        ("      conflict.py", "Tabelas judge_conflicts e conflict_records"),
        ("      audit.py", "Tabela audit_logs (append-only)"),
        ("    schemas/", "Schemas Pydantic v2 para validacao de request/response"),
        ("    services/", "Logica de negocio pura — chamada pelos routers"),
        ("      lottery_engine.py", "KERNEL: algoritmo completo de sorteio (8 passos)"),
        ("      user_service.py", "CRUD de usuarios com validacoes"),
        ("      process_service.py", "Ciclo de vida dos processos"),
        ("      conflict_service.py", "Recusa de juiz, juiz temporario"),
        ("      audit_service.py", "Escrita no AuditLog"),
        ("    jobs/", "Tarefas agendadas"),
        ("      scheduler.py", "APScheduler + lifespan do FastAPI"),
        ("    routers/", "Endpoints FastAPI organizados por modulo"),
        ("      auth.py", "POST /auth/login"),
        ("      users.py", "CRUD /users/ (somente TI)"),
        ("      processes.py", "Gerenciamento de processos"),
        ("      conflicts.py", "Recusa, juiz temporario"),
        ("      audit.py", "Consulta ao AuditLog"),
        ("    utils/", "Funcoes auxiliares reutilizaveis"),
        ("      document_validator.py", "Validacao de CPF e CNPJ"),
        ("      business_days.py", "Calculo do proximo dia util"),
        ("    main.py", "Entrada da aplicacao — cria o app FastAPI"),
        ("  seed.py", "Script de dados iniciais (usuarios + LotteryState)"),
        ("  alembic.ini", "Configuracao do Alembic"),
        ("  .env.example", "Modelo de arquivo de variaveis de ambiente"),
        ("  requirements.txt", "Dependencias Python do projeto"),
    ]

    for path, desc in estrutura:
        is_dir = path.strip().endswith("/")
        indent = len(path) - len(path.lstrip())
        cor_texto = AZUL_MEDIO if is_dir else CINZA_ESCURO
        fonte = "Courier-Bold" if is_dir else "Courier"
        row = Table(
            [[
                Paragraph(path,
                          ParagraphStyle("fp", fontName=fonte, fontSize=8,
                                         textColor=cor_texto,
                                         leftIndent=indent * 2)),
                Paragraph(desc,
                          ParagraphStyle("fd", fontName="Helvetica", fontSize=8,
                                         textColor=CINZA_MEDIO)),
            ]],
            colWidths=[9 * cm, 7.5 * cm],
        )
        row.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ("LINEBELOW", (0, 0), (-1, -1), 0.2, colors.HexColor("#f3f4f6")),
        ]))
        story.append(row)

    # =========================================================================
    # CAP 3 — CONFIGURACOES E AMBIENTE
    # =========================================================================
    story.append(PageBreak())
    story.append(secao_colorida("3. Configuracoes e Ambiente — app/core/config.py", AZUL_MEDIO, BRANCO, e))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        "Este arquivo centraliza <b>todas</b> as configuracoes da aplicacao. "
        "Usa a biblioteca <b>pydantic-settings</b>, que carrega automaticamente "
        "as variaveis do arquivo <code>.env</code> e valida os tipos na inicializacao. "
        "Se uma variavel obrigatoria faltar ou tiver tipo errado, a aplicacao nao sobe.",
        e["body"]
    ))

    story.append(Paragraph("Como funciona o pydantic-settings:", e["h3"]))
    story.append(Paragraph(
        "A classe <b>Settings</b> herda de <b>BaseSettings</b>. "
        "Cada atributo da classe eh uma variavel de ambiente. "
        "O <b>Field(...)</b> define o valor padrao e uma descricao legivel. "
        "A classe interna <b>Config</b> diz de onde ler o arquivo .env.",
        e["body"]
    ))

    story.append(Paragraph("Variaveis de Ambiente:", e["h3"]))
    story.append(tabela_campos(
        ["Variavel", "Padrao", "Descricao"],
        [
            ["DATABASE_URL", "postgresql+asyncpg://...", "URL async para a aplicacao (asyncpg)"],
            ["SYNC_DATABASE_URL", "postgresql://...", "URL sincrona para o Alembic (psycopg2)"],
            ["SECRET_KEY", "troque-esta-chave...", "Chave para assinar tokens JWT — TROQUE EM PRODUCAO"],
            ["ALGORITHM", "HS256", "Algoritmo de assinatura JWT"],
            ["ACCESS_TOKEN_EXPIRE_HOURS", "8", "Horas ate o token expirar"],
            ["UPLOAD_DIR", "./uploads", "Pasta para documentos de conflito"],
            ["ENVIRONMENT", "development", "development = SQL no console; production = sem SQL"],
        ],
        e,
        larguras=[5 * cm, 4 * cm, 7.5 * cm],
    ))

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "ATENCAO: O objeto <b>settings</b> e instanciado uma unica vez no final do arquivo "
        "e importado por todos os outros modulos. Nunca instancie Settings() novamente — "
        "use sempre <code>from app.core.config import settings</code>.",
        e["aviso"]
    ))

    story.append(caixa_codigo([
        "# Uso correto em qualquer modulo:",
        "from app.core.config import settings",
        "",
        "print(settings.DATABASE_URL)       # postgresql+asyncpg://...",
        "print(settings.ACCESS_TOKEN_EXPIRE_HOURS)  # 8",
    ], e))

    # =========================================================================
    # CAP 4 — BANCO DE DADOS
    # =========================================================================
    story.append(PageBreak())
    story.append(secao_colorida("4. Banco de Dados — app/core/database.py", AZUL_MEDIO, BRANCO, e))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        "Este modulo cria os tres elementos fundamentais para o acesso ao banco de dados "
        "de forma assincrona. Tudo usa <b>SQLAlchemy 2.0</b> com suporte nativo a async/await.",
        e["body"]
    ))

    conceitos = [
        ("engine", "Objeto de conexao com o PostgreSQL. Gerencia um pool de conexoes. "
         "echo=True imprime as queries SQL — util para depurar em desenvolvimento."),
        ("AsyncSessionLocal", "Fabrica de sessoes: cada chamada a AsyncSessionLocal() cria "
         "uma sessao isolada. expire_on_commit=False evita que objetos fiquem invalidos "
         "apos o commit."),
        ("Base", "Classe pai de todos os modelos SQLAlchemy. Ao herdar de Base, o modelo "
         "e registrado nos metadados que o Alembic usa para gerar migrations."),
    ]
    for nome, desc in conceitos:
        story.append(KeepTogether([
            Paragraph(f"<b>{nome}</b>", e["h3"]),
            Paragraph(desc, e["body"]),
        ]))

    story.append(Paragraph("Por que duas URLs de banco de dados?", e["h3"]))
    story.append(tabela_campos(
        ["URL", "Driver", "Quando usar"],
        [
            ["DATABASE_URL", "asyncpg", "Aplicacao FastAPI em tempo de execucao — todas as queries async"],
            ["SYNC_DATABASE_URL", "psycopg2", "Alembic para rodar migrations — o Alembic nao suporta async"],
        ],
        e,
        larguras=[4.5 * cm, 3 * cm, 9 * cm],
    ))

    story.append(Spacer(1, 0.2 * cm))
    story.append(caixa_codigo([
        "# Como o pool_pre_ping funciona:",
        "# Antes de cada query, o SQLAlchemy envia um SELECT 1",
        "# Se a conexao caiu (timeout), ele reconecta automaticamente.",
        "# Sem isso: erros aleatorios apos periodos de inatividade.",
        "",
        "engine = create_async_engine(",
        "    settings.DATABASE_URL,",
        "    echo=(settings.ENVIRONMENT == 'development'),",
        "    pool_pre_ping=True,",
        ")",
    ], e))

    # =========================================================================
    # CAP 5 — SEGURANCA
    # =========================================================================
    story.append(PageBreak())
    story.append(secao_colorida("5. Seguranca — app/core/security.py", AZUL_MEDIO, BRANCO, e))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("Hash de Senhas com bcrypt", e["h2"]))
    story.append(Paragraph(
        "O bcrypt e um algoritmo de hash projetado especificamente para senhas. "
        "Diferente de MD5 ou SHA-256, ele e <b>intencionalmente lento</b> — "
        "o que dificulta ataques de forca bruta. Cada hash inclui um 'salt' aleatorio "
        "embutido, entao duas senhas iguais geram hashes diferentes.",
        e["body"]
    ))

    story.append(caixa_codigo([
        "# Criando hash:",
        "hash = hash_password('minhasenha123')",
        "# Resultado: $2b$12$abc123...xyz (60 caracteres, inclui o salt)",
        "",
        "# Verificando senha:",
        "ok = verify_password('minhasenha123', hash)  # True",
        "ok = verify_password('senhaerrada',  hash)  # False",
    ], e))

    story.append(Paragraph("JSON Web Token (JWT)", e["h2"]))
    story.append(Paragraph(
        "Um JWT e um token compacto e autocontido que carrega informacoes do usuario. "
        "Tem tres partes separadas por pontos: <b>Header</b> (algoritmo), "
        "<b>Payload</b> (dados do usuario) e <b>Signature</b> (assinatura digital). "
        "O servidor assina o token com SECRET_KEY — qualquer alteracao invalida a assinatura.",
        e["body"]
    ))

    story.append(tabela_campos(
        ["Campo no Payload", "Descricao"],
        [
            ["sub", "ID do usuario (UUID como string) — campo padrao JWT para 'subject'"],
            ["role", "Papel do usuario (ex: JUDGE) — apenas informativo no token"],
            ["judge_id", "ID do juiz vinculado (para assessores) ou null"],
            ["exp", "Timestamp de expiracao — adicionado automaticamente pelo create_access_token"],
        ],
        e,
        larguras=[4 * cm, 12.5 * cm],
    ))

    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "IMPORTANTE: A validacao real do role e feita buscando o usuario no banco de dados "
        "(deps.py), nao lendo o campo 'role' do token. Isso garante que um token nao "
        "possa ser manipulado para obter privilegios.",
        e["aviso"]
    ))

    # =========================================================================
    # CAP 6 — DEPENDENCIAS FASTAPI
    # =========================================================================
    story.append(PageBreak())
    story.append(secao_colorida("6. Dependencias FastAPI — app/core/deps.py", AZUL_MEDIO, BRANCO, e))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        "O FastAPI tem um sistema de injecao de dependencias poderoso. "
        "Funcoes com <b>Depends()</b> sao executadas automaticamente antes do handler "
        "de cada requisicao, recebendo seus resultados como parametros.",
        e["body"]
    ))

    deps = [
        ("get_db", "Abre uma sessao async do banco no inicio da requisicao e garante "
         "que ela sera fechada ao final, mesmo em caso de erro (bloco try/finally). "
         "Cada requisicao tem sua propria sessao isolada."),
        ("get_current_user", "Extrai o token JWT do header Authorization, decodifica, "
         "busca o usuario no banco e valida se esta ativo. "
         "Retorna o objeto User completo ou levanta HTTP 401."),
        ("require_roles(*roles)", "Fabrica de dependencias para RBAC. "
         "Aceita um ou mais UserRole e cria uma dependencia que verifica se o "
         "usuario logado tem um dos roles permitidos. Levanta HTTP 403 se negado."),
    ]
    for nome, desc in deps:
        story.append(KeepTogether([
            Paragraph(f"<b>{nome}</b>", e["h3"]),
            Paragraph(desc, e["body"]),
        ]))

    story.append(caixa_codigo([
        "# Uso nos routers:",
        "",
        "# Apenas TI acessa esta rota:",
        "@router.get('/')",
        "async def listar(current_user = require_roles(UserRole.TI)):",
        "    ...",
        "",
        "# TI ou JUDGE podem acessar:",
        "@router.post('/reopen')",
        "async def reabrir(current_user = require_roles(UserRole.TI, UserRole.JUDGE)):",
        "    ...",
        "",
        "# Sessao de banco injetada automaticamente:",
        "@router.get('/{id}')",
        "async def obter(id: UUID, db: AsyncSession = Depends(get_db)):",
        "    ...",
    ], e))

    # =========================================================================
    # CAP 7 — MODELOS SQLALCHEMY
    # =========================================================================
    story.append(PageBreak())
    story.append(secao_colorida("7. Modelos SQLAlchemy — app/models/", VERDE, BRANCO, e))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        "Os modelos definem a estrutura das tabelas do banco de dados. "
        "Usam a sintaxe moderna do SQLAlchemy 2.0 com <b>Mapped</b> e <b>mapped_column</b> "
        "para tipagem estatica. Todos herdam de <b>Base</b> (database.py).",
        e["body"]
    ))

    # User
    story.append(Paragraph("7.1 — User (users)", e["h2"]))
    story.append(Paragraph(
        "Representa todos os usuarios do sistema. O campo <b>role</b> define "
        "o nivel de acesso. O campo <b>judge_id</b> e uma auto-referencia: "
        "assessores apontam para o juiz ao qual estao vinculados.",
        e["body"]
    ))
    story.append(tabela_campos(
        ["Campo", "Tipo SQL", "Descricao"],
        [
            ["id", "UUID (PK)", "Chave primaria gerada automaticamente (uuid4)"],
            ["name", "VARCHAR(200)", "Nome completo do usuario"],
            ["email", "VARCHAR(200)", "Email unico e indexado — usado no login"],
            ["password_hash", "VARCHAR(200)", "Hash bcrypt da senha — nunca armazena senha em texto puro"],
            ["role", "VARCHAR(20)", "Papel: TI | JUDGE | ASSESSOR | ASSISTANT | TEMP_JUDGE"],
            ["is_active", "BOOLEAN", "False = soft-delete (sem remover do banco)"],
            ["judge_id", "UUID (FK users.id)", "Juiz vinculado — obrigatorio para ASSESSOR, null para outros"],
            ["created_at", "TIMESTAMP", "Data de criacao (automatica)"],
            ["updated_at", "TIMESTAMP", "Data da ultima atualizacao (automatica no onupdate)"],
        ],
        e,
        larguras=[3.5 * cm, 3.5 * cm, 9.5 * cm],
    ))

    # Person
    story.append(Paragraph("7.2 — Person (persons)", e["h2"]))
    story.append(Paragraph(
        "Representa a parte interessada em um processo judicial. "
        "O documento (CPF ou CNPJ) e unico no sistema. "
        "Os juizes podem ter conflito de interesse com uma Person especifica.",
        e["body"]
    ))
    story.append(tabela_campos(
        ["Campo", "Tipo SQL", "Descricao"],
        [
            ["id", "UUID (PK)", "Chave primaria"],
            ["name", "VARCHAR(200)", "Nome da pessoa fisica ou juridica"],
            ["document", "VARCHAR(20)", "CPF (11 digitos) ou CNPJ (14 digitos) sem formatacao"],
            ["document_type", "VARCHAR(5)", "CPF ou CNPJ"],
            ["created_at", "TIMESTAMP", "Data de cadastro"],
        ],
        e,
        larguras=[3.5 * cm, 3.5 * cm, 9.5 * cm],
    ))

    # Process
    story.append(Paragraph("7.3 — Process (processes)", e["h2"]))
    story.append(Paragraph(
        "Tabela central do sistema. Registra o ciclo de vida completo de um processo "
        "judicial, desde o cadastro ate o encerramento. Tem tres chaves estrangeiras "
        "para users (juiz atual, juiz temporario, juiz original).",
        e["body"]
    ))
    story.append(tabela_campos(
        ["Campo", "Tipo SQL", "Descricao"],
        [
            ["id", "UUID (PK)", "Chave primaria"],
            ["process_number", "VARCHAR(50)", "Numero unico do processo — indexado"],
            ["level", "INTEGER", "1=BASIC | 2=INTERMEDIATE | 3=COMPLEX"],
            ["status", "VARCHAR(30)", "Estado atual (ver ciclo de vida abaixo)"],
            ["person_id", "UUID (FK)", "Parte do processo (referencia persons)"],
            ["assigned_judge_id", "UUID (FK)", "Juiz atual responsavel pelo processo"],
            ["temp_judge_id", "UUID (FK)", "Juiz temporario (quando todos os titulares recusaram)"],
            ["original_judge_id", "UUID (FK)", "Juiz original — guardado para reabertura futura"],
            ["lottery_scheduled_at", "TIMESTAMP", "Data/hora do proximo sorteio (dia util as 10h)"],
            ["assigned_at", "TIMESTAMP", "Quando o juiz foi atribuido"],
            ["created_by_id", "UUID (FK)", "Quem cadastrou o processo"],
            ["created_at / updated_at", "TIMESTAMP", "Datas de criacao e ultima atualizacao"],
        ],
        e,
        larguras=[4 * cm, 3.5 * cm, 9 * cm],
    ))

    story.append(Paragraph("Ciclo de Vida do Status:", e["h3"]))
    ciclo = [
        ("PENDING_LOTTERY", "Estado inicial — processo criado, aguardando sorteio"),
        ("SCHEDULED", "Sorteio agendado (reservado para uso futuro)"),
        ("ASSIGNED", "Juiz atribuido pelo sorteio"),
        ("IN_PROGRESS", "Processo em andamento com o juiz"),
        ("CLOSED", "Processo encerrado"),
        ("REOPENED", "Processo reaberto — proximo sorteio vai para o juiz original"),
        ("CONFLICT_PENDING", "Todos os juizes recusaram — aguarda nomeacao de temporario"),
        ("TEMP_ASSIGNED", "Juiz temporario nomeado pelo TI"),
    ]
    story.append(tabela_campos(["Status", "Significado"], ciclo, e, larguras=[4.5 * cm, 12 * cm]))

    # LotteryRound e LotteryState
    story.append(Paragraph("7.4 — LotteryRound e LotteryState (lottery.py)", e["h2"]))
    story.append(Paragraph(
        "<b>LotteryRound</b> e o historico: cada sorteio realizado gera um registro nesta tabela. "
        "E possivel ver quantos sorteios um processo teve e qual juiz foi selecionado em cada um.",
        e["body"]
    ))
    story.append(Paragraph(
        "<b>LotteryState</b> e o estado global do algoritmo — sempre tem exatamente 1 linha "
        "(singleton). Usa tres colunas JSONB para armazenar estruturas dinamicas que mudam "
        "a cada sorteio:",
        e["body"]
    ))
    story.append(tabela_campos(
        ["Campo JSONB", "Tipo", "Descricao"],
        [
            ["complex_round_participants", "list[str]",
             "IDs dos juizes que ja receberam um processo COMPLEX na rodada atual. "
             "Resetado quando todos os 8 participarem."],
            ["judge_priorities", "dict[str, int]",
             "Juizes com prioridade no proximo sorteio. "
             "Chave = judge_id, Valor = nivel do processo. "
             "Adicionado quando um juiz recusa; removido quando a prioridade e usada."],
            ["judge_weighted_sums", "dict[str, int]",
             "Soma de pesos dos processos de cada juiz. "
             "Usado para verificar balanceamento de carga. "
             "BASIC=1, INTERMEDIATE=2, COMPLEX=3."],
        ],
        e,
        larguras=[4.5 * cm, 3 * cm, 9 * cm],
    ))

    story.append(Paragraph(
        "IMPORTANTE: Colunas JSONB nao sao rastreadas automaticamente pelo SQLAlchemy "
        "quando modificadas in-place. Por isso, toda vez que um campo JSONB e alterado, "
        "chamamos <b>flag_modified(state, 'nome_do_campo')</b> para forcar a deteccao "
        "da mudanca e garantir que o UPDATE seja enviado ao banco.",
        e["aviso"]
    ))

    # Conflict e Audit
    story.append(Paragraph("7.5 — JudgeConflict e ConflictRecord (conflict.py)", e["h2"]))
    story.append(Paragraph(
        "<b>JudgeConflict</b>: relacao pre-cadastrada de proximidade entre um juiz e uma pessoa. "
        "O TI registra isso antes do sorteio para garantir que o juiz nunca sera selecionado "
        "para processos envolvendo essa pessoa.",
        e["body"]
    ))
    story.append(Paragraph(
        "<b>ConflictRecord</b>: criado quando um juiz recusa formalmente um processo durante "
        "o sorteio. Inclui justificativa e caminho do documento comprobatorio salvo em disco.",
        e["body"]
    ))

    story.append(Paragraph("7.6 — AuditLog (audit.py)", e["h2"]))
    story.append(Paragraph(
        "Registra todas as acoes relevantes do sistema. E APPEND-ONLY — "
        "nenhuma entrada e modificada ou deletada. O campo <b>details</b> e JSONB "
        "para armazenar dados contextuais em formato livre.",
        e["body"]
    ))
    story.append(tabela_campos(
        ["Action registrada", "Quando ocorre"],
        [
            ["LOGIN / LOGOUT", "Usuario faz login ou logout"],
            ["USER_CREATED / UPDATED / DEACTIVATED", "TI gerencia usuarios"],
            ["PROCESS_CREATED / UPDATED / REOPENED", "Assistente ou TI gerencia processos"],
            ["LOTTERY_SUCCESS", "Sorteio executado com sucesso"],
            ["LOTTERY_REOPEN_ASSIGNED", "Processo reaberto — juiz original reatribuido"],
            ["LOTTERY_ALL_CONFLICT", "Todos os juizes recusaram o processo"],
            ["CONFLICT_REFUSED", "Juiz recusou formalmente um processo"],
            ["TEMP_JUDGE_ASSIGNED", "TI nomeou juiz temporario"],
            ["TEMP_ACCESS_CLOSED", "TI encerrou acesso do juiz temporario"],
            ["BALANCE_ALERT", "Diferenca de carga entre juizes ultrapassou 3 pontos"],
            ["ASSESSOR_LINKED", "Assessor vinculado a um juiz"],
        ],
        e,
        larguras=[6 * cm, 10.5 * cm],
    ))

    # =========================================================================
    # CAP 9 — KERNEL DE SORTEIO (pagina propria, destaque maximo)
    # =========================================================================
    story.append(PageBreak())
    story.append(secao_colorida(
        "9. Kernel de Sorteio — app/services/lottery_engine.py",
        ROXO, BRANCO, e
    ))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        "Este e o modulo mais critico do sistema. A funcao <b>run_lottery()</b> implementa "
        "o algoritmo completo de sorteio em 8 passos sequenciais. "
        "E chamada tanto pelo APScheduler (automaticamente) quanto pela rota "
        "POST /processes/{id}/run-lottery (manualmente, para testes).",
        e["body"]
    ))

    passos = [
        ("PASSO 1", "Carregar Dados",
         "Busca o processo pelo ID e valida que tem status PENDING_LOTTERY ou REOPENED. "
         "Carrega todos os juizes ativos (role=JUDGE, is_active=True) e o LotteryState singleton. "
         "Se o processo nao existir ou tiver status invalido, a funcao retorna silenciosamente."),
        ("PASSO 2", "Atalho REOPENED",
         "Se o processo foi reaberto (REOPENED) e tem original_judge_id definido, "
         "o processo e atribuido diretamente ao juiz original — sem sorteio aleatorio. "
         "Registra no LotteryRound e AuditLog, commita e RETORNA (nao continua o algoritmo)."),
        ("PASSO 3a", "Filtro de Conflito",
         "Busca os JudgeConflicts pre-cadastrados para a Person do processo. "
         "Remove da lista de elegiveis todos os juizes com conflito registrado."),
        ("PASSO 3b", "Rodizio COMPLEX",
         "Se o processo for nivel COMPLEX: verifica quantos juizes ja participaram "
         "da rodada atual. Se todos (8) ja participaram, reinicia a lista. "
         "Remove da lista elegivel os que ja participaram nesta rodada."),
        ("PASSO 3c", "Prioridade Certeira",
         "Verifica se algum juiz elegivel tem prioridade para este nivel de processo "
         "(foi gerada quando o juiz recusou um processo do mesmo nivel). "
         "Se sim, este juiz sera selecionado com certeza — a prioridade e entao removida."),
        ("PASSO 4", "Verificar Elegiveis",
         "Se a lista de elegiveis estiver vazia (todos tem conflito), "
         "o processo vai para CONFLICT_PENDING e o audit log e registrado. "
         "A funcao retorna sem atribuir nenhum juiz."),
        ("PASSO 5", "Selecionar Juiz",
         "Se ha prioridade, usa o juiz prioritario. "
         "Caso contrario, usa random.choice() na lista de elegiveis. "
         "O Python garante distribuicao uniforme com random.choice."),
        ("PASSO 6", "Atribuir Processo",
         "Define assigned_judge_id e original_judge_id no processo. "
         "Muda status para ASSIGNED e registra o timestamp assigned_at. "
         "Atualiza complex_round_participants e judge_weighted_sums no LotteryState. "
         "Usa flag_modified() em todos os campos JSONB alterados."),
        ("PASSO 7", "Registrar Historico",
         "Cria uma entrada em LotteryRound com o juiz selecionado e o numero da rodada. "
         "Registra LOTTERY_SUCCESS no AuditLog com detalhes do sorteio. "
         "Commita todas as mudancas no banco."),
        ("PASSO 8", "Alerta de Balanceamento",
         "Apos o commit, verifica as somas ponderadas de todos os juizes. "
         "Se a diferenca entre o maximo e o minimo for maior que 3, "
         "registra BALANCE_ALERT no AuditLog para revisao pela TI."),
    ]

    for passo, titulo, desc in passos:
        cor_bg = ROXO_CLARO if passo.startswith("PASSO 3") else CINZA_CLARO
        row = Table(
            [[
                Paragraph(f"<b>{passo}</b>",
                          ParagraphStyle("pp", fontName="Helvetica-Bold",
                                         fontSize=9, textColor=ROXO, alignment=TA_CENTER)),
                Paragraph(f"<b>{titulo}</b><br/>{desc}",
                          ParagraphStyle("pd", fontName="Helvetica",
                                         fontSize=9, textColor=CINZA_ESCURO, leading=14)),
            ]],
            colWidths=[2.5 * cm, 14 * cm],
        )
        row.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), ROXO_CLARO),
            ("BACKGROUND", (1, 0), (1, 0), cor_bg),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ]))
        story.append(row)

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Pseudo-codigo resumido do algoritmo:", e["h3"]))
    story.append(caixa_codigo([
        "async def run_lottery(process_id, db):",
        "    process = await buscar_processo(process_id)",
        "    if process.status nao em {PENDING_LOTTERY, REOPENED}: return",
        "    all_judges = await buscar_juizes_ativos()",
        "    state = await carregar_lottery_state()",
        "",
        "    # Atalho para processo reaberto",
        "    if process.status == REOPENED and process.original_judge_id:",
        "        atribuir(process, original_judge_id) → commit → return",
        "",
        "    # Filtragem de elegiveis",
        "    eligible = [j for j in all_judges se j.id nao tem conflito com process.person]",
        "    if process.level == COMPLEX:",
        "        eligible = [j for j in eligible se j nao participou da rodada atual]",
        "    priority_judge = verificar_prioridade(eligible, state, process.level)",
        "",
        "    if not eligible: → status CONFLICT_PENDING → commit → return",
        "",
        "    # Selecao",
        "    selected = priority_judge ou random.choice(eligible)",
        "",
        "    # Atualizacao",
        "    process.assigned_judge_id = selected.id",
        "    process.original_judge_id = selected.id",
        "    process.status = ASSIGNED",
        "    atualizar_lottery_state(state, selected, process.level)  # flag_modified!",
        "    criar_lottery_round(process, selected)",
        "    await db.commit()",
        "",
        "    verificar_balanceamento(state.judge_weighted_sums)",
    ], e))

    # =========================================================================
    # CAP 10 — SERVICOS DE NEGOCIO
    # =========================================================================
    story.append(PageBreak())
    story.append(secao_colorida("10. Servicos de Negocio — app/services/", VERDE, BRANCO, e))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        "Os servicos contem a logica de negocio pura, separada das rotas HTTP. "
        "Os routers chamam os servicos, que por sua vez interagem com os modelos. "
        "Isso facilita testes unitarios e reutilizacao da logica.",
        e["body"]
    ))

    servicos = [
        ("audit_service.py", "Funcao log() — cria entradas no AuditLog. "
         "Nao faz commit — deixa o chamador decidir quando commitar. "
         "Aceita user_id=None para acoes automaticas do scheduler."),
        ("user_service.py", "CRUD completo: get_user_by_id, get_user_by_email, "
         "get_all_users, create_user (com hash de senha), update_user, "
         "deactivate_user (soft-delete), link_assessor_to_judge. "
         "Todas as operacoes registram no AuditLog."),
        ("process_service.py", "create_process (calcula lottery_scheduled_at automaticamente), "
         "get_processes (filtrado por role), get_process_by_id, "
         "update_process (ASSISTANT so pode se PENDING_LOTTERY), "
         "reopen_process (muda para REOPENED e reagenda sorteio), "
         "get_process_history."),
        ("conflict_service.py", "refuse_process (salva documento, cria ConflictRecord, "
         "adiciona prioridade, verifica se todos recusaram), "
         "assign_temp_judge (valida role TEMP_JUDGE ou JUDGE), "
         "close_temp_access (remove temp_judge_id, volta para ASSIGNED), "
         "get_conflicts_for_person (usado pelo kernel)."),
    ]
    story.append(tabela_campos(
        ["Arquivo", "Responsabilidades"],
        servicos, e,
        larguras=[4.5 * cm, 12 * cm],
    ))

    # =========================================================================
    # CAP 11 — SCHEDULER
    # =========================================================================
    story.append(PageBreak())
    story.append(secao_colorida("11. Agendador de Tarefas — app/jobs/scheduler.py", LARANJA, BRANCO, e))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        "O APScheduler executa tarefas em background de forma automatica. "
        "O sistema usa <b>BackgroundScheduler</b> (thread separada) com "
        "<b>CronTrigger</b> para disparar o sorteio nos horarios corretos.",
        e["body"]
    ))

    story.append(Paragraph("Desafio: Async dentro de Sincrono", e["h2"]))
    story.append(Paragraph(
        "O APScheduler 3.x e sincrono, mas o codigo do FastAPI e async. "
        "A solucao e usar <b>asyncio.run()</b> dentro da funcao do scheduler — "
        "isso cria um novo event loop para executar as corrotinas. "
        "As importacoes sao feitas localmente (dentro da funcao) para evitar "
        "import circular na inicializacao do modulo.",
        e["body"]
    ))

    story.append(caixa_codigo([
        "def run_pending_lotteries():    # funcao sincrona — rodada numa thread",
        "    # imports locais evitam circular import",
        "    from app.core.database import AsyncSessionLocal",
        "    from app.services.lottery_engine import run_lottery",
        "",
        "    async def _executar_sorteios():   # corrotina interna",
        "        async with AsyncSessionLocal() as db:",
        "            processos = await buscar_pendentes(db)",
        "            for p in processos:",
        "                await run_lottery(p.id, db)",
        "",
        "    asyncio.run(_executar_sorteios())  # cria event loop temporario",
    ], e))

    story.append(Paragraph("Padrao lifespan do FastAPI", e["h2"]))
    story.append(Paragraph(
        "O gerenciador de contexto <b>lifespan</b> substitui os antigos "
        "@app.on_event('startup') e @app.on_event('shutdown'). "
        "O codigo antes do yield roda quando o servidor inicia; "
        "o codigo apos o yield roda quando o servidor para.",
        e["body"]
    ))

    story.append(caixa_codigo([
        "@asynccontextmanager",
        "async def lifespan(app):",
        "    # === STARTUP ===",
        "    scheduler.add_job(",
        "        run_pending_lotteries,",
        "        CronTrigger(day_of_week='mon-fri', hour=10, minute=0,",
        "                    timezone='America/Sao_Paulo'),",
        "        id='daily_lottery',",
        "        replace_existing=True,",
        "    )",
        "    scheduler.start()",
        "",
        "    yield  # servidor rodando aqui",
        "",
        "    # === SHUTDOWN ===",
        "    scheduler.shutdown(wait=False)",
    ], e))

    # =========================================================================
    # CAP 12 — ROUTERS
    # =========================================================================
    story.append(PageBreak())
    story.append(secao_colorida("12. Routers (Endpoints) — app/routers/", AZUL_MEDIO, BRANCO, e))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("Mapa completo de endpoints e permissoes:", e["h2"]))
    story.append(tabela_campos(
        ["Metodo", "Rota", "Roles", "Descricao"],
        [
            ["POST", "/auth/login", "Publico", "Login — retorna token JWT"],
            ["POST", "/auth/logout", "Qualquer", "Registra logout no audit"],
            ["GET", "/users/", "TI", "Lista todos os usuarios"],
            ["POST", "/users/", "TI", "Cria usuario com hash de senha"],
            ["PUT", "/users/{id}", "TI", "Atualiza dados do usuario"],
            ["DELETE", "/users/{id}", "TI", "Soft-delete (is_active=False)"],
            ["POST", "/users/{id}/link-assessor", "TI", "Vincula assessor ao juiz"],
            ["POST", "/processes/", "ASSISTANT, TI", "Cadastra processo, agenda sorteio"],
            ["GET", "/processes/", "TI, JUDGE, ASSESSOR", "Lista (filtrado por role)"],
            ["GET", "/processes/{id}", "TI, JUDGE, ASSESSOR, TEMP_JUDGE", "Detalhe — TEMP_JUDGE so o seu"],
            ["PUT", "/processes/{id}", "ASSISTANT, ASSESSOR, TI", "Edita — ASSISTANT so PENDING_LOTTERY"],
            ["POST", "/processes/{id}/reopen", "TI, JUDGE", "Reabre — proximo sorteio vai ao original"],
            ["GET", "/processes/{id}/history", "TI, JUDGE, ASSESSOR", "Historico de sorteios"],
            ["POST", "/processes/{id}/run-lottery", "TI", "Forca sorteio manual (testes)"],
            ["POST", "/conflicts/refuse", "JUDGE", "Recusa formal com documento (multipart)"],
            ["POST", "/conflicts/assign-temp-judge", "TI", "Nomeia juiz temporario"],
            ["POST", "/conflicts/close-temp-access/{id}", "TI", "Encerra acesso temporario"],
            ["POST", "/conflicts/pre-register", "TI", "Cadastra conflito de proximidade"],
            ["GET", "/conflicts/judge/{id}", "TI", "Lista conflitos de um juiz"],
            ["GET", "/audit/logs", "TI", "Todos os logs (paginados)"],
            ["GET", "/audit/logs/{entity}/{id}", "TI, JUDGE, ASSESSOR", "Logs de uma entidade"],
            ["GET", "/health", "Publico", "Verificacao de saude da aplicacao"],
        ],
        e,
        larguras=[1.5 * cm, 5.5 * cm, 4 * cm, 5.5 * cm],
    ))

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Regra especial: TEMP_JUDGE", e["h3"]))
    story.append(Paragraph(
        "O juiz temporario so pode acessar o GET /processes/{id} do processo "
        "ao qual foi especificamente designado. O router verifica explicitamente "
        "se process.temp_judge_id == current_user.id antes de retornar os dados. "
        "Juizes titulares (JUDGE) nao tem essa restricao — podem ver qualquer processo.",
        e["body"]
    ))

    story.append(Paragraph("Recusa de processo: multipart/form-data", e["h3"]))
    story.append(Paragraph(
        "A rota POST /conflicts/refuse recebe dados via multipart/form-data "
        "(nao JSON). Isso permite enviar o arquivo de documento junto com os campos textuais. "
        "O FastAPI usa Form() para campos de texto e File() para o arquivo. "
        "O arquivo e salvo em /uploads/{process_id}/{timestamp}_{filename}.",
        e["body"]
    ))

    # =========================================================================
    # CAP 13 — UTILITARIOS
    # =========================================================================
    story.append(PageBreak())
    story.append(secao_colorida("13. Utilitarios — app/utils/", AZUL_MEDIO, BRANCO, e))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("13.1 — Validacao de CPF (document_validator.py)", e["h2"]))
    story.append(Paragraph(
        "Implementa o algoritmo oficial da Receita Federal para validar CPF. "
        "Remove formatacao automaticamente (pontos, traco). "
        "Rejeita sequencias repetidas (111.111.111-11 etc.).",
        e["body"]
    ))
    story.append(tabela_campos(
        ["Etapa", "Descricao"],
        [
            ["Limpeza", "Remove todos os caracteres nao-numericos com regex \\D"],
            ["Tamanho", "Verifica se tem exatamente 11 digitos"],
            ["Sequencia", "Rejeita CPFs como 000...000, 111...111 (todos iguais)"],
            ["1 digito", "Soma digitos[0..8] x pesos[10..2]; resto = (soma*10)%11; digito = 0 se resto>=10"],
            ["2 digito", "Soma digitos[0..9] x pesos[11..2]; resto = (soma*10)%11; digito = 0 se resto>=10"],
        ],
        e,
        larguras=[3 * cm, 13.5 * cm],
    ))

    story.append(Paragraph("13.2 — Validacao de CNPJ (document_validator.py)", e["h2"]))
    story.append(Paragraph(
        "Algoritmo oficial da Receita Federal para CNPJ. "
        "Diferente do CPF, usa dois conjuntos de pesos distintos.",
        e["body"]
    ))
    story.append(tabela_campos(
        ["Etapa", "Descricao"],
        [
            ["Limpeza", "Remove todos os caracteres nao-numericos"],
            ["Tamanho", "Verifica 14 digitos"],
            ["Sequencia", "Rejeita CNPJs como 00.000.000/0000-00"],
            ["1 digito", "Pesos1=[5,4,3,2,9,8,7,6,5,4,3,2]; digito=0 se resto<2 senao 11-resto"],
            ["2 digito", "Pesos2=[6,5,4,3,2,9,8,7,6,5,4,3,2]; digito=0 se resto<2 senao 11-resto"],
        ],
        e,
        larguras=[3 * cm, 13.5 * cm],
    ))

    story.append(Paragraph("13.3 — Dias Uteis (business_days.py)", e["h2"]))
    story.append(Paragraph(
        "Calcula a data/hora do proximo sorteio (proximo dia util as 10:00). "
        "Considera apenas segunda a sexta (sem feriados nesta versao).",
        e["body"]
    ))
    story.append(tabela_campos(
        ["Cenario", "Resultado"],
        [
            ["Segunda as 08:00", "Segunda as 10:00 (mesmo dia, antes das 10h)"],
            ["Segunda as 11:00", "Terca as 10:00 (ja passou das 10h)"],
            ["Sexta as 15:00", "Segunda as 10:00 (pula sabado e domingo)"],
            ["Sabado qualquer hora", "Segunda as 10:00 (fim de semana)"],
        ],
        e,
        larguras=[5 * cm, 11.5 * cm],
    ))

    # =========================================================================
    # CAP 14 — SEED
    # =========================================================================
    story.append(PageBreak())
    story.append(secao_colorida("14. Seed Inicial — seed.py", VERDE, BRANCO, e))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        "O seed.py cria os dados iniciais necessarios para o sistema funcionar. "
        "Deve ser executado UMA VEZ apos rodar as migrations. "
        "E idempotente: se os usuarios ja existirem, apenas pula e nao duplica.",
        e["body"]
    ))

    story.append(tabela_campos(
        ["Usuario criado", "Email", "Senha", "Role"],
        [
            ["Administrador TI", "ti@tribunal.gov.br", "Admin@2025", "TI"],
            ["Juiz Titular 01", "judge01@tribunal.gov.br", "Judge@2025", "JUDGE"],
            ["Juiz Titular 02", "judge02@tribunal.gov.br", "Judge@2025", "JUDGE"],
            ["... (juizes 03 a 07)", "judge03..07@tribunal.gov.br", "Judge@2025", "JUDGE"],
            ["Juiz Titular 08", "judge08@tribunal.gov.br", "Judge@2025", "JUDGE"],
            ["Assessor 01", "assessor01@tribunal.gov.br", "Assessor@2025", "ASSESSOR (judge01)"],
            ["Assistente 01", "assistente01@tribunal.gov.br", "Assist@2025", "ASSISTANT"],
        ],
        e,
        larguras=[4 * cm, 5.5 * cm, 3 * cm, 4 * cm],
    ))

    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "Alem dos usuarios, o seed cria o LotteryState singleton com todos os "
        "campos JSONB vazios: complex_round_participants=[], judge_priorities={}, "
        "judge_weighted_sums={}.",
        e["nota"]
    ))

    # =========================================================================
    # CAP 15 — ALEMBIC
    # =========================================================================
    story.append(PageBreak())
    story.append(secao_colorida("15. Alembic (Migrations) — alembic/env.py", AZUL_MEDIO, BRANCO, e))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        "O Alembic detecta diferencas entre os modelos SQLAlchemy e o banco de dados "
        "e gera scripts de migracao automaticamente. Usa a URL SINCRONA porque "
        "o Alembic nao suporta drivers async nativamente.",
        e["body"]
    ))

    story.append(Paragraph("Configuracao do env.py:", e["h3"]))
    story.append(tabela_campos(
        ["Elemento", "Funcao"],
        [
            ["load_dotenv()", "Carrega o arquivo .env antes de qualquer coisa"],
            ["config.set_main_option('sqlalchemy.url', sync_url)", "Usa SYNC_DATABASE_URL do .env, nao o valor do alembic.ini"],
            ["import app.models", "Importa TODOS os modelos para que o autogenerate os detecte"],
            ["target_metadata = Base.metadata", "Diz ao Alembic qual e o estado 'alvo' (os modelos Python)"],
            ["run_migrations_offline()", "Gera SQL sem conectar ao banco — para revisao"],
            ["run_migrations_online()", "Executa as migrations diretamente no banco"],
        ],
        e,
        larguras=[4.5 * cm, 12 * cm],
    ))

    story.append(Paragraph("Comandos principais:", e["h3"]))
    story.append(caixa_codigo([
        "# Gerar uma nova migration (detecta mudancas nos modelos):",
        "alembic revision --autogenerate -m 'descricao_da_mudanca'",
        "",
        "# Aplicar todas as migrations pendentes:",
        "alembic upgrade head",
        "",
        "# Ver o status atual:",
        "alembic current",
        "",
        "# Reverter a ultima migration:",
        "alembic downgrade -1",
        "",
        "# Ver historico de migrations:",
        "alembic history --verbose",
    ], e))

    # =========================================================================
    # CAP 16 — COMO EXECUTAR
    # =========================================================================
    story.append(PageBreak())
    story.append(secao_colorida("16. Como Executar o Sistema", AZUL_ESCURO, BRANCO, e))
    story.append(Spacer(1, 0.3 * cm))

    passos_exec = [
        ("1", "Instalar dependencias",
         "pip install -r requirements.txt"),
        ("2", "Configurar variaveis de ambiente",
         "cp .env.example .env\n# Edite .env com os dados do seu PostgreSQL"),
        ("3", "Criar o banco de dados no PostgreSQL",
         "psql -U postgres -c \"CREATE DATABASE sorteiapro;\""),
        ("4", "Gerar e aplicar migrations",
         "alembic revision --autogenerate -m \"initial\"\nalembic upgrade head"),
        ("5", "Popular dados iniciais",
         "python seed.py"),
        ("6", "Iniciar o servidor",
         "uvicorn app.main:app --reload --port 8000"),
        ("7", "Acessar o Swagger UI",
         "Abra http://localhost:8000/docs no navegador\nClique em 'Authorize' e faca login"),
    ]

    for num, titulo, cmd in passos_exec:
        bloco = KeepTogether([
            Table(
                [[
                    Paragraph(f"<b>{num}</b>",
                              ParagraphStyle("pn", fontName="Helvetica-Bold",
                                             fontSize=14, textColor=BRANCO, alignment=TA_CENTER)),
                    Paragraph(f"<b>{titulo}</b>",
                              ParagraphStyle("pt", fontName="Helvetica-Bold",
                                             fontSize=11, textColor=AZUL_ESCURO)),
                ]],
                colWidths=[1.2 * cm, 15.3 * cm],
                style=TableStyle([
                    ("BACKGROUND", (0, 0), (0, 0), AZUL_MEDIO),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ("LEFTPADDING", (0, 0), (0, 0), 6),
                    ("LEFTPADDING", (1, 0), (1, 0), 10),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]),
            ),
            caixa_codigo(cmd.split("\n"), e),
            Spacer(1, 0.2 * cm),
        ])
        story.append(bloco)

    # =========================================================================
    # CAP 17 — FLUXOS PRINCIPAIS
    # =========================================================================
    story.append(PageBreak())
    story.append(secao_colorida("17. Fluxos Principais do Sistema", AZUL_ESCURO, BRANCO, e))
    story.append(Spacer(1, 0.3 * cm))

    fluxos = [
        ("Fluxo 1: Cadastro e Sorteio Normal",
         [
             "ASSISTANT faz POST /processes/ com number, level, person_id",
             "Sistema calcula lottery_scheduled_at = proximo dia util 10:00",
             "Processo criado com status PENDING_LOTTERY",
             "No dia/hora agendados, o APScheduler dispara run_pending_lotteries()",
             "run_lottery() e chamado para o processo",
             "Juizes elegiveis sao filtrados (sem conflito com a Person)",
             "Para COMPLEX: aplica rodizio",
             "random.choice() seleciona o juiz",
             "Processo atualizado: status=ASSIGNED, assigned_judge_id=juiz",
             "LotteryRound e AuditLog registrados",
         ]),
        ("Fluxo 2: Recusa por Conflito de Interesse",
         [
             "Juiz recebe notificacao do processo atribuido",
             "JUDGE faz POST /conflicts/refuse (multipart: process_id, justification, document)",
             "Documento salvo em /uploads/{process_id}/{timestamp}_{filename}",
             "ConflictRecord criado",
             "judge_id adicionado em LotteryState.judge_priorities com o nivel do processo",
             "Sistema conta quantos juizes ja recusaram este processo",
             "Se ainda ha juizes disponiveis: reagenda lottery_scheduled_at para amanha 10:00",
             "Se TODOS recusaram: processo vai para CONFLICT_PENDING + audit log",
         ]),
        ("Fluxo 3: Nomeacao de Juiz Temporario",
         [
             "Processo com status CONFLICT_PENDING (todos recusaram)",
             "TI faz POST /conflicts/assign-temp-judge com process_id e temp_judge_user_id",
             "Sistema valida que o usuario tem role TEMP_JUDGE ou JUDGE",
             "Processo atualizado: status=TEMP_ASSIGNED, temp_judge_id=usuario",
             "TEMP_JUDGE pode agora acessar GET /processes/{id} (so este processo)",
             "Quando o caso encerra: TI faz POST /conflicts/close-temp-access/{id}",
             "temp_judge_id removido, status volta para ASSIGNED",
         ]),
        ("Fluxo 4: Reabertura de Processo",
         [
             "Processo esta com status CLOSED",
             "TI ou JUDGE faz POST /processes/{id}/reopen com justificativa",
             "Status muda para REOPENED",
             "lottery_scheduled_at recalculado para o proximo dia util",
             "Na hora do sorteio, run_lottery() detecta status=REOPENED",
             "Verifica process.original_judge_id (guardado na primeira atribuicao)",
             "Atribui diretamente ao juiz original — sem sorteio aleatorio",
             "Status volta para ASSIGNED",
         ]),
    ]

    for titulo, passos_fluxo in fluxos:
        story.append(Paragraph(titulo, e["h2"]))
        for i, passo in enumerate(passos_fluxo, 1):
            story.append(Paragraph(f"{i}. {passo}", e["bullet"]))
        story.append(Spacer(1, 0.3 * cm))

    # =========================================================================
    # CAP 18 — CHECKLIST
    # =========================================================================
    story.append(PageBreak())
    story.append(secao_colorida("18. Checklist de Regras de Negocio Implementadas", VERDE, BRANCO, e))
    story.append(Spacer(1, 0.3 * cm))

    checklist = [
        (True, "Sorteio automatico APScheduler (seg-sex 10:00 America/Sao_Paulo)"),
        (True, "Rodizio COMPLEX com complex_round_participants no LotteryState"),
        (True, "BASIC e INTERMEDIATE sem restricao de rodizio"),
        (True, "Processo REOPENED atribuido diretamente ao original_judge_id"),
        (True, "Conflito: documento salvo em /uploads + ConflictRecord no banco"),
        (True, "Prioridade certeira apos recusa (judge_priorities no LotteryState)"),
        (True, "Todos conflitados → status CONFLICT_PENDING + LOTTERY_ALL_CONFLICT no audit"),
        (True, "TEMP_JUDGE acessa SOMENTE o processo ao qual foi designado (check no router)"),
        (True, "Juizes titulares PODEM ver processo com temp_judge_id (sem restricao)"),
        (True, "ASSISTANT NAO pode listar /processes/ (403 no get_processes)"),
        (True, "ASSISTANT so edita processos com status PENDING_LOTTERY"),
        (True, "flag_modified() em todos os campos JSONB do LotteryState"),
        (True, "Validacao de CPF com algoritmo oficial da Receita Federal"),
        (True, "Validacao de CNPJ com algoritmo oficial da Receita Federal"),
        (True, "next_business_day() exclui sabado (5) e domingo (6)"),
        (True, "AuditLog APPEND-ONLY — sem rotas DELETE ou UPDATE"),
        (True, "Swagger em /docs com todos os endpoints documentados"),
        (True, "RBAC com require_roles() em todos os endpoints protegidos"),
        (True, "Soft-delete de usuarios (is_active=False, dado historico preservado)"),
        (True, "Alerta de balanceamento quando max-min de pesos > 3 (BALANCE_ALERT)"),
        (True, "lottery_scheduled_at calculado automaticamente ao criar processo"),
        (True, "Sorteio manual via POST /processes/{id}/run-lottery (apenas TI)"),
        (True, "ASSESSOR lista processos do juiz vinculado (judge_id)"),
        (True, "Seed idempotente — nao duplica dados se executado novamente"),
    ]

    for ok, item in checklist:
        cor_check = VERDE if ok else LARANJA
        simbolo = "[OK]" if ok else "[--]"
        row = Table(
            [[
                Paragraph(f"<b>{simbolo}</b>",
                          ParagraphStyle("cs", fontName="Helvetica-Bold",
                                         fontSize=9, textColor=cor_check,
                                         alignment=TA_CENTER)),
                Paragraph(item, ParagraphStyle("ci", fontName="Helvetica",
                                               fontSize=9, textColor=CINZA_ESCURO)),
            ]],
            colWidths=[1.2 * cm, 15.3 * cm],
        )
        row.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(row)

    story.append(Spacer(1, 0.5 * cm))
    story.append(Table(
        [[Paragraph(
            "Todos os 24 itens do checklist estao implementados e verificados. "
            "Sintaxe Python validada em todos os 39 arquivos .py do projeto.",
            ParagraphStyle("final", fontName="Helvetica-Bold", fontSize=10,
                           textColor=VERDE, alignment=TA_CENTER)
        )]],
        colWidths=[16.5 * cm],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), VERDE_CLARO),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("BOX", (0, 0), (-1, -1), 1.5, VERDE),
        ]),
    ))

    # =========================================================================
    # CONSTRUCAO FINAL
    # =========================================================================
    # Remove o placeholder da capa
    story.pop(0)

    doc.build(
        story,
        onFirstPage=capa,
        onLaterPages=add_page_number,
    )
    print(f"PDF gerado: {output_path}")


if __name__ == "__main__":
    build_pdf("SorteiaPro_Documentacao_Tecnica.pdf")

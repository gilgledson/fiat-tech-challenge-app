"""
Gera o PDF de entrega da Fase 3 (Portal do Aluno):
links dos 4 repositórios, link do vídeo, links das documentações e
confirmação do colaborador soat-architecture.

Uso: python docs/gerar_pdf_entrega_fase3.py
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, ListFlowable, ListItem,
    Image, PageBreak
)
from reportlab.lib.enums import TA_CENTER

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(BASE_DIR, "docs", "entrega-fase-3.pdf")
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "docs", "screenshots")

SCREENSHOTS = [
    ("newrelic-dashboard-negocio.png",
     "Dashboard \"Oficina API - Visão Geral\" — volume de OS, tempo médio por status e latência das APIs"),
    ("newrelic-dashboard-erros-uptime.png",
     "Dashboard \"Oficina API - Visão Geral\" — erros/falhas por endpoint e uptime do healthcheck (100%)"),
    ("newrelic-k8s-cluster-overview.png",
     "Kubernetes Cluster Explorer — visão geral do cluster AKS (pods, nodes, deployments)"),
    ("newrelic-k8s-cpu-mem-nodes.png",
     "Kubernetes Cluster Explorer — consumo de CPU/memória por nó"),
]

# ── Preencher antes de gerar o PDF final ────────────────────────────────────
VIDEO_URL = "https://drive.google.com/file/d/1UD4ez7I80B7l3tExast0C0Fk66_rkDFQ/view?usp=sharing"
# ─────────────────────────────────────────────────────────────────────────

REPOS = [
    ("Aplicação principal (Kubernetes)", "oficina-app",
     "https://github.com/gilgledson/fiat-tech-challenge-app"),
    ("Infraestrutura Kubernetes (Terraform)", "oficina-infra-kubernetes",
     "https://github.com/gilgledson/fiat-tech-challenge-infra-kubernetes"),
    ("Infraestrutura do Banco de Dados Gerenciado (Terraform)", "oficina-infra-banco-dados",
     "https://github.com/gilgledson/fiat-tech-challenge-infra-database"),
    ("Lambda / Function Serverless (autenticação por CPF)", "oficina-lambda-auth-cpf",
     "https://github.com/gilgledson/fiat-tech-challenge-lambda-auth-cpf"),
]

DOC_BASE = "https://github.com/gilgledson/fiat-tech-challenge-app/blob/main/docs/architecture"

DOCS = [
    ("Índice da documentação de arquitetura", f"{DOC_BASE}/README.md"),
    ("Diagrama de Componentes", f"{DOC_BASE}/diagrama-componentes.png"),
    ("Diagrama de Sequência — Autenticação por CPF", f"{DOC_BASE}/diagrama-sequencia-autenticacao-cpf.png"),
    ("Diagrama de Sequência — Abertura de Ordem de Serviço", f"{DOC_BASE}/diagrama-sequencia-abertura-os.png"),
    ("Diagrama ER (DER)", f"{DOC_BASE}/der-oficina-api.png"),
    ("RFC-001 — Escolha da nuvem", f"{DOC_BASE}/rfc-001-escolha-da-nuvem.md"),
    ("RFC-002 — Escolha do banco de dados", f"{DOC_BASE}/rfc-002-escolha-do-banco-de-dados.md"),
    ("RFC-003 — Estratégia de autenticação", f"{DOC_BASE}/rfc-003-estrategia-de-autenticacao.md"),
    ("ADR-001 — Padrão de comunicação", f"{DOC_BASE}/adr-001-padrao-de-comunicacao.md"),
    ("ADR-002 — Uso de HPA", f"{DOC_BASE}/adr-002-uso-de-hpa.md"),
    ("ADR-003 — Plano de hospedagem da Function", f"{DOC_BASE}/adr-003-function-app-service-plan.md"),
    ("ADR-004 — JWT compartilhado entre serviços", f"{DOC_BASE}/adr-004-jwt-compartilhado-entre-servicos.md"),
    ("Justificativa formal do banco de dados", f"{DOC_BASE}/justificativa-banco-de-dados.md"),
]

styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    "TitleCustom", parent=styles["Title"], fontSize=20, spaceAfter=6,
)
subtitle_style = ParagraphStyle(
    "SubtitleCustom", parent=styles["Normal"], fontSize=11,
    textColor=colors.HexColor("#555555"), alignment=TA_CENTER, spaceAfter=20,
)
heading_style = ParagraphStyle(
    "HeadingCustom", parent=styles["Heading2"], fontSize=13,
    spaceBefore=18, spaceAfter=6, textColor=colors.HexColor("#1a1a1a"),
)
body_style = ParagraphStyle(
    "BodyCustom", parent=styles["Normal"], fontSize=11, leading=16,
)
link_style = ParagraphStyle(
    "LinkCustom", parent=styles["Normal"], fontSize=10, leading=15,
    textColor=colors.HexColor("#1a56db"),
)
item_label_style = ParagraphStyle(
    "ItemLabelCustom", parent=styles["Normal"], fontSize=10.5, leading=15,
)
warn_style = ParagraphStyle(
    "WarnCustom", parent=styles["Normal"], fontSize=10, leading=14,
    textColor=colors.HexColor("#b91c1c"), spaceBefore=4,
)
caption_style = ParagraphStyle(
    "CaptionCustom", parent=styles["Normal"], fontSize=9,
    textColor=colors.HexColor("#777777"), alignment=TA_CENTER, spaceBefore=6,
)

story = []

story.append(Paragraph("Oficina API — Tech Challenge Fase 3", title_style))
story.append(Paragraph(
    "Entrega: API Gateway, autenticação serverless, observabilidade, "
    "repositórios segregados com CI/CD e documentação de arquitetura",
    subtitle_style,
))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#dddddd")))
story.append(Spacer(1, 12))

# 1. Repositórios
story.append(Paragraph("1. Repositórios", heading_style))
story.append(Paragraph(
    "Projeto organizado em 4 repositórios separados, cada um com CI/CD "
    "próprio (GitHub Actions):",
    body_style,
))
repo_items = []
for descricao, nome, url in REPOS:
    repo_items.append(ListItem(Paragraph(
        f'<b>{nome}</b> — {descricao}<br/><link href="{url}">{url}</link>',
        item_label_style,
    ), spaceAfter=8))
story.append(ListFlowable(repo_items, bulletType="bullet", leftIndent=14))

story.append(Paragraph(
    "O usuário <b>soat-architecture</b> foi adicionado como colaborador em "
    "todos os 4 repositórios acima.",
    body_style,
))

# 2. Vídeo de demonstração
story.append(Paragraph("2. Vídeo de Demonstração", heading_style))
story.append(Paragraph(
    "Vídeo (até 15 minutos) demonstrando: autenticação com CPF, execução da "
    "pipeline CI/CD, deploy automatizado, consumo das APIs protegidas, "
    "dashboard de monitoramento com análise ao vivo, e logs/traces em "
    "execução:",
    body_style,
))
story.append(Paragraph(VIDEO_URL, link_style))
if "SUBSTITUIR" in VIDEO_URL:
    story.append(Paragraph(
        "⚠ Atualize VIDEO_URL neste script com o link real antes de gerar "
        "a versão final deste PDF.",
        warn_style,
    ))

# 3. Documentação da arquitetura
story.append(Paragraph("3. Documentação da Arquitetura", heading_style))
story.append(Paragraph(
    "Diagramas de componentes e sequência, RFCs, ADRs, diagrama ER e "
    "justificativa formal do banco de dados — todos no repositório da "
    "aplicação principal (<b>oficina-app</b>), pasta docs/architecture:",
    body_style,
))
doc_items = []
for nome, url in DOCS:
    doc_items.append(ListItem(Paragraph(
        f'{nome}<br/><link href="{url}">{url}</link>',
        item_label_style,
    ), spaceAfter=6))
story.append(ListFlowable(doc_items, bulletType="bullet", leftIndent=14))

# 4. Evidências de observabilidade (New Relic)
story.append(Paragraph("4. Observabilidade — New Relic (evidências)", heading_style))
story.append(Paragraph(
    "Capturas de tela do dashboard e do monitoramento de recursos do "
    "Kubernetes, ambos em produção:",
    body_style,
))
for filename, caption in SCREENSHOTS:
    path = os.path.join(SCREENSHOTS_DIR, filename)
    if os.path.exists(path):
        story.append(PageBreak())
        img = Image(path)
        max_width = 16 * cm
        max_height = 20 * cm
        ratio = img.imageHeight / img.imageWidth
        width, height = max_width, max_width * ratio
        if height > max_height:
            height = max_height
            width = max_height / ratio
        img.drawWidth = width
        img.drawHeight = height
        story.append(img)
        story.append(Paragraph(caption, caption_style))
    else:
        story.append(Paragraph(f"[Screenshot não encontrado: {path}]", body_style))

doc = SimpleDocTemplate(
    OUTPUT_PATH, pagesize=A4,
    topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
)
doc.build(story)
print(f"PDF gerado em: {OUTPUT_PATH}")

"""
Gera o PDF de entrega da Fase 2 (portal do aluno):
link do repositório + desenho de arquitetura + link do vídeo.

Uso: python docs/gerar_pdf_entrega.py
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIAGRAM_PATH = os.path.join(BASE_DIR, "docs", "diagrama-arquitetura-infraestrutura.png")
OUTPUT_PATH = os.path.join(BASE_DIR, "docs", "entrega-fase-2.pdf")

REPO_URL = "https://github.com/gilgledson/fiat-tech-challenge-ddd"
VIDEO_URL = "https://drive.google.com/file/d/1TqMzNbciNb-3_zPpxVR6hI0vbInDfhIA/view?usp=sharing"

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
    "LinkCustom", parent=styles["Normal"], fontSize=11, leading=16,
    textColor=colors.HexColor("#1a56db"),
)
caption_style = ParagraphStyle(
    "CaptionCustom", parent=styles["Normal"], fontSize=9,
    textColor=colors.HexColor("#777777"), alignment=TA_CENTER, spaceBefore=6,
)

story = []

story.append(Paragraph("Oficina API — Tech Challenge Fase 2", title_style))
story.append(Paragraph("Entrega: infraestrutura, orquestração e automação", subtitle_style))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#dddddd")))
story.append(Spacer(1, 16))

story.append(Paragraph("1. Repositório", heading_style))
story.append(Paragraph(
    "Repositório GitHub (compartilhado com o usuário <b>soat-architecture</b>):",
    body_style,
))
story.append(Paragraph(f'<link href="{REPO_URL}">{REPO_URL}</link>', link_style))

story.append(Paragraph("2. Desenho da Arquitetura", heading_style))
story.append(Paragraph(
    "Componentes da aplicação, infraestrutura provisionada (Terraform → AKS + "
    "Azure Postgres Flexible Server) e fluxo de deploy (GitHub Actions → Docker "
    "Hub → Kubernetes):",
    body_style,
))
story.append(PageBreak())
if os.path.exists(DIAGRAM_PATH):
    img = Image(DIAGRAM_PATH)
    max_width = 16 * cm
    max_height = 22 * cm
    ratio = img.imageHeight / img.imageWidth
    width, height = max_width, max_width * ratio
    if height > max_height:
        height = max_height
        width = max_height / ratio
    img.drawWidth = width
    img.drawHeight = height
    story.append(img)
    story.append(Paragraph("Diagrama de arquitetura de infraestrutura", caption_style))
else:
    story.append(Paragraph(
        f"[Diagrama não encontrado em {DIAGRAM_PATH} — gere antes de rodar este script]",
        body_style,
    ))

story.append(Paragraph("3. Vídeo Demonstrativo", heading_style))
story.append(Paragraph(
    "Vídeo (até 15 minutos) demonstrando: deploy da aplicação, execução do "
    "CI/CD, consumo das APIs e escalabilidade automática:",
    body_style,
))
story.append(Paragraph(VIDEO_URL, link_style))

doc = SimpleDocTemplate(
    OUTPUT_PATH, pagesize=A4,
    topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
)
doc.build(story)
print(f"PDF gerado em: {OUTPUT_PATH}")

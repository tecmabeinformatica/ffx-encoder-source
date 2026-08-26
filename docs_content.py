from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


OUT_DIR = Path(r"D:\scripts\Projeto APP\FFX Encoder 3.0.0 Python\dist\FFX Encoder 3.0")


GUIDE_SECTIONS = [
    ("VisÃ£o Geral", [
        "O FFX Encoder 3.0.10 Ã© uma ferramenta para conversÃ£o, organizaÃ§Ã£o e finalizaÃ§Ã£o de arquivos de vÃ­deo, com foco em produtividade para tarefas repetitivas.",
        "Todos os arquivos processados sÃ£o salvos na pasta Saida, preservando os arquivos originais.",
    ]),
    ("Formas de Uso", [
        "Menu de contexto: clique com o botÃ£o direito em uma pasta e escolha Abrir com FFX Encoder 3.0.",
        "FFX Encoder Aqui.exe: copie esse arquivo para qualquer pasta de vÃ­deos e execute para abrir o programa diretamente naquela pasta.",
    ]),
    ("Audio e Legendas", [
        "Manter apenas Ã¡udio 1, Ã¡udio 2 ou Ã¡udio em portuguÃªs.",
        "Manter Ã¡udio PT+EN e legenda PT.",
        "Juntar vÃ­deo com legenda externa sem recodificaÃ§Ã£o.",
        "Extrair Ã¡udio em formato original, AAC 224 kbps ou MP3 320 kbps.",
        "Juntar Ã¡udio externo com opÃ§Ã£o de idioma, faixa default e atraso/adiantamento em milissegundos.",
        "Extrair legendas embutidas manualmente ou todas de uma vez.",
        "Remover legendas embutidas selecionadas sem recodificar o vÃ­deo.",
        "Remover a mesma posiÃ§Ã£o de legenda em lote, com resumo e confirmaÃ§Ã£o antes do processamento.",
        "Gerar relatÃ³rio clean de faixas de Ã¡udio e legenda de todos os vÃ­deos da pasta.",
    ]),
    ("Converter", [
        "Converte vÃ­deos para H.265/HEVC, H.264/AVC ou AV1.",
        "Permite escolher MKV ou MP4 como container de saÃ­da.",
        "Permite copiar o Ã¡udio original ou converter para AAC 224 kbps.",
        "Preserva o mÃ¡ximo possÃ­vel de Ã¡udios e legendas compatÃ­veis.",
        "Em MP4, anexos e legendas incompatÃ­veis podem ser ignorados automaticamente.",
    ]),
    ("Upscale 1080p", [
        "Aumenta a resoluÃ§Ã£o de vÃ­deos abaixo de 1080p para 1080p.",
        "Usa as mesmas escolhas de codec, container, Ã¡udio e qualidade da funÃ§Ã£o Converter.",
        "VÃ­deos que jÃ¡ estÃ£o em 1080p ou acima sÃ£o ignorados.",
    ]),
    ("Deinterlace, Denoise e Remaster", [
        "Deinterlace permite manter a resoluÃ§Ã£o original ou aplicar upscaling para 1080p.",
        "Denoise reduz granulado em nÃ­veis leve, mÃ©dio ou forte.",
        "Remaster aplica uma combinaÃ§Ã£o de reduÃ§Ã£o de ruÃ­do, nitidez e ajustes visuais.",
    ]),
    ("Capas", [
        "Usar cover local com arquivos cover.jpg, cover.jpeg ou cover.png.",
        "Buscar capa automaticamente no TMDb.",
        "Digitar nome manualmente para busca no TMDb.",
        "Buscar capa no cache local.",
        "Remover capas embutidas.",
        "Ao aplicar uma capa, capas antigas sÃ£o substituÃ­das quando possÃ­vel, evitando acÃºmulo de anexos.",
    ]),
    ("Metadados", [
        "Limpar metadados indesejados, preservando idiomas e flags das faixas.",
        "Inserir metadados corretos de filmes pelo TMDb.",
        "A funÃ§Ã£o TMDb tambÃ©m aplica capa do filme quando disponÃ­vel.",
    ]),
    ("Modo Inteligente (Filmes)", [
        "Rotina criada para preparar um filme com menos etapas manuais.",
        "Verifica legenda externa, mantÃ©m Ã¡udio PT+EN e legenda PT, limpa metadados antigos e insere metadados/capa pelo TMDb.",
        "Foi pensada para uso com um filme por pasta.",
    ]),
    ("Pastas de SaÃ­da", [
        "Convertidos: Saida\\Convertidos",
        "Upscale: Saida\\Upscale",
        "Deinterlace: Saida\\Deinterlace",
        "Denoise: Saida\\Denoise",
        "Remaster: Saida\\Remaster",
        "Capas: Saida\\Capas",
        "Metadados: Saida\\Metadados",
        "Modo Inteligente: Saida\\Modo_Inteligente",
        "Legendas extraÃ­das: Saida\\Legendas\\Extraidas",
        "Legendas removidas: Saida\\Legendas\\Removidas",
    ]),
]


NOTES_SECTIONS = [
    ("Resumo", [
        "O FFX Encoder 3.0.10 continua a linha reconstruÃ­da e repaginada da ferramenta, mantendo o FFmpeg como motor principal e melhorando a organizaÃ§Ã£o das funÃ§Ãµes.",
        "A versÃ£o foi preparada para instalaÃ§Ã£o em C:\\FFX Encoder, com menu de contexto e opÃ§Ã£o alternativa via FFX Encoder Aqui.exe.",
    ]),
    ("Novidades Principais", [
        "Nova base reconstruÃ­da e mais organizada.",
        "ExecutÃ¡vel empacotado, sem necessidade de instalar Python separadamente.",
        "FFmpeg e FFprobe incluÃ­dos no pacote.",
        "InstalaÃ§Ã£o padrÃ£o em C:\\FFX Encoder.",
        "Novo FFX Encoder Aqui.exe para abrir a ferramenta em qualquer pasta sem depender do menu de contexto.",
        "Adicionado desinstalador e correção na remoção do menu de contexto.",
        "O desinstalador agora preserva a pasta Capas, mantendo o cache local entre versões.",
        "Menu principal mais limpo, exibindo apenas o encoder detectado.",
        "Cores no console para avisos, erros, sucesso e processos.",
    ]),
    ("Audio e Legendas", [
        "Adicionada extraÃ§Ã£o de legendas embutidas.",
        "Adicionada remoÃ§Ã£o de legendas embutidas selecionadas.",
        "Adicionada remoÃ§Ã£o de legendas em lote por posiÃ§Ã£o, com prÃ©via e confirmaÃ§Ã£o.",
        "Adicionado relatÃ³rio de faixas de Ã¡udio e legenda, salvo em Saida\\Relatorios.",
        "Adicionada funÃ§Ã£o Organizar faixas para ajustar idioma, default e forced em Ã¡udio/legendas sem recode.",
        "Adicionado Editor de Faixas para escolher manualmente o que manter/remover e ajustar idioma/default/forced em um unico remux.",
        "O Editor de Faixas agora permite mover faixas para cima ou para baixo dentro do mesmo tipo.",
        "O Editor de Faixas agora aceita selecao multipla, intervalos, atalhos de limpeza e resumo antes de aplicar.",
        "Corrigida a ordem das faixas em PT+EN: Ã¡udio portuguÃªs agora fica como primeira faixa e default.",
        "Modo Inteligente tambÃ©m passa a gerar o Ã¡udio portuguÃªs como primeira faixa e default.",
        "Melhorada a compatibilidade ao juntar legenda externa, normalizando legendas de texto antes da muxagem.",
        "A legenda externa agora é posicionada antes de capas/streams extras para evitar falhas de exibição em players como MPC.",
        "Melhor tratamento de idiomas, faixas ausentes e mensagens de erro.",
        "Suporte a atraso/adiantamento em milissegundos ao juntar Ã¡udio externo e legenda externa.",
    ]),
    ("ConversÃ£o e Processamento", [
        "FunÃ§Ã£o Converter com H.265, H.264 e AV1.",
        "Escolha de MKV ou MP4.",
        "Escolha de Ã¡udio copy ou AAC 224 kbps.",
        "Melhor compatibilidade com MP4, ignorando anexos e legendas incompatÃ­veis quando necessÃ¡rio.",
        "Upscale 1080p com as mesmas opÃ§Ãµes principais de conversÃ£o.",
    ]),
    ("Capas e TMDb", [
        "Busca de capas pelo TMDb.",
        "Busca automÃ¡tica por sÃ©ries, filmes e temporadas quando possÃ­vel.",
        "Cache local de capas.",
        "AplicaÃ§Ã£o de capas substituindo capas anteriores quando possÃ­vel.",
        "RemoÃ§Ã£o de capas embutidas em lote.",
    ]),
    ("Metadados", [
        "Limpeza de metadados indesejados preservando idiomas e flags das faixas.",
        "InserÃ§Ã£o de metadados de filmes pelo TMDb.",
        "AplicaÃ§Ã£o de capa junto aos metadados de filme.",
        "RenomeaÃ§Ã£o da saÃ­da de acordo com o tÃ­tulo e ano retornados pelo TMDb.",
    ]),
    ("Modo Inteligente", [
        "Novo Modo Inteligente (Filmes), reunindo etapas comuns em uma rotina Ãºnica.",
        "Pensado para preparar um filme final com Ã¡udio, legenda, capa e metadados organizados.",
    ]),
    ("ObservaÃ§Ãµes", [
        "Arquivos originais continuam preservados.",
        "Para mÃ¡xima compatibilidade com mÃºltiplas faixas, legendas e capas, o formato MKV continua sendo recomendado.",
        "FunÃ§Ãµes TMDb exigem conexÃ£o com a internet.",
    ]),
]


def build_pdf(path: Path, title: str, subtitle: str, sections: list[tuple[str, list[str]]]) -> None:
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="DocTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#1f4e79"),
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="Subtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#555555"),
        spaceAfter=16,
    ))
    styles.add(ParagraphStyle(
        name="Section",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#1f4e79"),
        spaceBefore=10,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="Body",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
        spaceAfter=4,
    ))

    story = [
        Paragraph(title, styles["DocTitle"]),
        Paragraph(subtitle, styles["Subtitle"]),
    ]
    for section_title, items in sections:
        story.append(Paragraph(section_title, styles["Section"]))
        for item in items:
            story.append(Paragraph(f"â€¢ {item}", styles["Body"]))
        story.append(Spacer(1, 4))

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=1.7 * cm,
        leftMargin=1.7 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=title,
        author="DjManeca",
    )
    doc.build(story)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    build_pdf(
        OUT_DIR / "FFX Encoder Guia Completo 3.0.10.pdf",
        "FFX Encoder",
        "Guia Completo de Funcionalidades - VersÃ£o 3.0.10",
        GUIDE_SECTIONS,
    )
    build_pdf(
        OUT_DIR / "FFX Encoder 3.0.10 Notas da Versao.pdf",
        "FFX Encoder 3.0.10",
        "Notas da VersÃ£o",
        NOTES_SECTIONS,
    )


if __name__ == "__main__":
    main()

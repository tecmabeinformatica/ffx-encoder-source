from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)


ROOT = Path(__file__).resolve().parent
VERSION = "2.1"
OUT_DIR = ROOT / "build" / "docs"
OUT_README = OUT_DIR / "FFX Encoder GUI Leia-me.pdf"
OUT_HELP = OUT_DIR / "FFX Encoder GUI Ajuda.pdf"


def register_fonts() -> tuple[str, str]:
    fonts = Path(r"C:\Windows\Fonts")
    regular = fonts / "arial.ttf"
    bold = fonts / "arialbd.ttf"
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("FFXRegular", str(regular)))
        pdfmetrics.registerFont(TTFont("FFXBold", str(bold)))
        return "FFXRegular", "FFXBold"
    return "Helvetica", "Helvetica-Bold"


FONT, FONT_BOLD = register_fonts()
BLUE = colors.HexColor("#1f4e79")
GRAY = colors.HexColor("#4a4a4a")
PALE_GRAY = colors.HexColor("#f4f6f7")
BORDER = colors.HexColor("#d0d7de")


def styles() -> dict[str, ParagraphStyle]:
    return {
        "title": ParagraphStyle(
            "title",
            fontName=FONT_BOLD,
            fontSize=24,
            leading=31,
            textColor=BLUE,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            fontName=FONT,
            fontSize=11,
            leading=16,
            textColor=GRAY,
            alignment=TA_CENTER,
            spaceAfter=14,
        ),
        "section": ParagraphStyle(
            "section",
            fontName=FONT_BOLD,
            fontSize=16,
            leading=24,
            textColor=BLUE,
            spaceBefore=16,
            spaceAfter=9,
        ),
        "body": ParagraphStyle(
            "body",
            fontName=FONT,
            fontSize=10.5,
            leading=15.5,
            alignment=TA_JUSTIFY,
            spaceAfter=7,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            fontName=FONT,
            fontSize=10.2,
            leading=15,
            leftIndent=14,
            firstLineIndent=-9,
            spaceAfter=4.5,
        ),
        "card_title": ParagraphStyle(
            "card_title",
            fontName=FONT_BOLD,
            fontSize=11,
            leading=18,
            textColor=BLUE,
            spaceBefore=6,
            spaceAfter=4,
        ),
        "card": ParagraphStyle(
            "card",
            fontName=FONT,
            fontSize=9.8,
            leading=14.2,
            textColor=colors.black,
            backColor=PALE_GRAY,
            borderColor=BORDER,
            borderWidth=0.6,
            borderPadding=8,
            spaceAfter=9,
        ),
    }


def safe_text(text: str) -> str:
    return escape(text).replace("\n", "<br/>")


def p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(safe_text(text), style)


def rich(text: str, style: ParagraphStyle) -> Paragraph:
    # Textos passados aqui já podem conter tags simples do ReportLab, como <b>.
    return Paragraph(text.replace("\n", "<br/>"), style)


def bullets(items: list[str], st: dict[str, ParagraphStyle]) -> list[Paragraph]:
    return [rich(f"• {item}", st["bullet"]) for item in items]


def card(title: str, text: str, st: dict[str, ParagraphStyle]) -> KeepTogether:
    return KeepTogether([
        p(title, st["card_title"]),
        rich(text, st["card"]),
    ])


def build_pdf(path: Path, title: str, subtitle: str, story: list) -> None:
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=1.75 * cm,
        leftMargin=1.75 * cm,
        topMargin=1.35 * cm,
        bottomMargin=1.35 * cm,
        title=title,
        author="DjManeca",
    )
    doc.build(story)


def build_readme() -> None:
    st = styles()
    story: list = [
        p("FFX Encoder GUI", st["title"]),
        p(f"Leia-me - Versão {VERSION}", st["subtitle"]),
        HRFlowable(width="100%", color=BLUE, thickness=1.2, spaceAfter=12),
        p(
            "O FFX Encoder GUI é uma ferramenta criada para organizar, converter e finalizar arquivos de vídeo "
            "com o FFmpeg. Ele reúne em uma interface gráfica tarefas que normalmente exigiriam vários comandos "
            "manuais, acelerando rotinas de áudio, legendas, capas, metadados, conversão, limpeza e remasterização.",
            st["body"],
        ),
        p(
            "O programa preserva os arquivos originais e grava os resultados em pastas de saída separadas por função. "
            "Isso facilita testes, revisões e organização de lotes grandes.",
            st["body"],
        ),
        p("Principais recursos", st["section"]),
        *bullets([
            "Conversão para H.265/HEVC, H.264/AVC e AV1, com saída em MKV ou MP4.",
            "Modo Vídeo copy na conversão para trocar apenas o áudio sem recodificar a imagem.",
            "Uso de encoder NVIDIA quando disponível, mantendo alternativa por CPU.",
            "Resoluções Original, 480p, 720p, 1080p, 1440p, 2160p e personalizada nas rotinas de encode.",
            "Opções de áudio em copy, AAC 256 kbps, AAC 320 kbps e AC3 640 kbps nas rotinas de encode.",
            "Ferramentas para manter, remover, extrair, organizar e reposicionar faixas de áudio e legendas.",
            "Editor de faixas com idioma, default, forced, remoção de anexos, imagens e legendas.",
            "Busca de capas e metadados pelo TMDb, com prévia visual e cache local de capas.",
            "Modo Inteligente Filme e Modo Inteligente Série para rotinas completas.",
            "Pastas personalizadas para saída e temporários, úteis em fluxos com discos diferentes.",
            "Aba Corrigir Aspecto para ajustar arquivos marcados ou encodados com proporção incorreta.",
            "Aba Corrigir Bordas para detectar automaticamente ou forçar cortes manuais de bordas.",
            "Relatórios de faixas para áudio, legendas, codecs, idiomas e flags.",
        ], st),
        p("Fluxos inteligentes", st["section"]),
        card(
            "Modo Inteligente Filme",
            "Prepara um filme único na pasta. A rotina verifica legenda externa, organiza áudio PT+EN e legenda PT, "
            "limpa metadados antigos e aplica metadados/capa do TMDb. O resultado é salvo em "
            "<b>Saida\\Modo_Inteligente</b>.",
            st,
        ),
        card(
            "Modo Inteligente Série",
            "Converte episódios da pasta conforme as opções escolhidas, mantém áudio PT+EN, mantém legenda em português, "
            "limpa metadados e aplica capa da série ou temporada quando disponível. O resultado é salvo em "
            "<b>Saida\\Modo_Inteligente_Serie</b>.",
            st,
        ),
        p(
            "Antes de executar modos inteligentes com TMDb, busque o resultado correto no painel Metadados e capas "
            "e confirme visualmente quando houver prévia de capa.",
            st["body"],
        ),
        p("Organização das saídas", st["section"]),
        rich(
            "Os resultados são criados dentro da pasta <b>Saida</b>, separados por função, como <b>Convertidos</b>, "
            "<b>Upscale</b>, <b>Deinterlace</b>, <b>Denoise</b>, <b>Remaster</b>, <b>Audio</b>, <b>Legendas</b>, "
            "<b>Capas</b>, <b>Metadados</b>, <b>Relatorios</b> e modos inteligentes.",
            st["body"],
        ),
        p(
            "A pasta raiz de saída e a pasta temporária podem ser configuradas em Configurações > Pastas de trabalho. "
            "Se nada for configurado, o comportamento padrão é mantido.",
            st["body"],
        ),
        p("Conversão com filtros combinados", st["section"]),
        p(
            "A aba Conversão permite aplicar deinterlace separado e escolher um filtro principal, como denoise ou "
            "remaster, junto com remoção de bordas e mudança de resolução em uma única etapa de encode. Isso evita "
            "recodificações repetidas e ajuda a preservar melhor a qualidade final.",
            st["body"],
        ),
        p("Remaster", st["section"]),
        p(
            "O Remaster continua disponível como filtro dentro da conversão para permitir codec, áudio, resolução, "
            "upscale e ajuste visual em uma única etapa. A aba Remaster é uma rotina mais direta, com presets leve, "
            "médio e forte, deinterlace opcional, opções de áudio e normalização de volume separada.",
            st["body"],
        ),
        *bullets([
            "Remaster leve agora é mais conservador, com limpeza e nitidez sutis para uso geral.",
            "Remaster médio fica próximo ao antigo leve, com melhoria mais perceptível e menor risco de aparência artificial.",
            "Remaster forte foi suavizado para casos mais fracos, mas ainda deve ser usado com cautela.",
            "A normalização de volume usa loudnorm para deixar o áudio mais regular.",
        ], st),
        p("Uso recomendado", st["section"]),
        *bullets([
            "Use MKV para preservar várias faixas de áudio, legendas, anexos e capas.",
            "Use MP4 para compatibilidade simples, aceitando limitações de legendas e anexos.",
            "Para arquivos muito bagunçados, limpe metadados e capas problemáticas antes de inserir novas faixas.",
            "Confira idioma, default e forced no editor de faixas quando o arquivo vier de fontes diferentes.",
            "Em séries, mantenha nomes como Nome da Série - S01E01 - Título do Episódio para melhorar a detecção.",
        ], st),
        p("TMDb e capas", st["section"]),
        p(
            "As funções online dependem de uma chave de leitura do TMDb configurada no menu do programa. As capas "
            "baixadas e aprovadas podem ser armazenadas em cache local para uso posterior.",
            st["body"],
        ),
        p("Observação importante", st["section"]),
        p(
            "O FFX Encoder GUI é uma ferramenta de organização e processamento de arquivos existentes no computador "
            "do usuário. Use apenas com arquivos sobre os quais você tenha direito de uso. O software não é destinado "
            "a burlar proteções, obter conteúdo ilegal ou substituir obrigações legais do usuário.",
            st["body"],
        ),
    ]
    build_pdf(OUT_README, "FFX Encoder GUI Leia-me", f"Leia-me - Versão {VERSION}", story)


def build_help() -> None:
    st = styles()
    story: list = [
        p("FFX Encoder GUI", st["title"]),
        p(f"Ajuda e problemas frequentes - Versão {VERSION}", st["subtitle"]),
        HRFlowable(width="100%", color=BLUE, thickness=1.2, spaceAfter=12),
        p(
            "Este guia reúne situações comuns, causas prováveis e caminhos seguros para resolver problemas durante "
            "o uso do FFX Encoder GUI.",
            st["body"],
        ),
        p("Problemas comuns e soluções", st["section"]),
        card(
            "Botão TMDb bloqueado",
            "Causa provável: chave TMDb não configurada.\n"
            "Como resolver: acesse <b>Configurações &gt; Chave TMDb</b> e informe seu token de leitura.",
            st,
        ),
        card(
            "Capa não encontrada",
            "Causa provável: o nome do arquivo não identifica bem o filme, série ou temporada.\n"
            "Como resolver: digite manualmente o nome no painel <b>Metadados e capas</b>, selecione o resultado correto "
            "e confira a prévia antes de aplicar.",
            st,
        ),
        card(
            "Áudio ou legenda faltando no resultado",
            "Causa provável: o arquivo original não tinha a faixa no idioma esperado, ou a faixa estava como idioma indefinido.\n"
            "Como resolver: use o relatório de faixas e o editor de faixas para conferir idiomas, default e forced antes de processar.",
            st,
        ),
        card(
            "MP4 ignorou alguma legenda",
            "Causa provável: o contêiner MP4 não aceita todos os tipos de legenda, anexos ou imagens.\n"
            "Como resolver: use MKV para máxima compatibilidade ou aceite que o MP4 leve apenas faixas compatíveis.",
            st,
        ),
        card(
            "Processo parece parado",
            "Causa provável: encodes longos podem demorar sem mudar imediatamente a saída.\n"
            "Como resolver: observe o indicador Processando e o log. Use Cancelar processo somente se tiver certeza.",
            st,
        ),
        card(
            "Arquivo já existe na saída",
            "Causa provável: a pasta de saída personalizada ou padrão já contém um arquivo com o mesmo nome.\n"
            "Como resolver: escolha entre sobrescrever, pular o arquivo, sobrescrever todos os conflitos do lote ou cancelar.",
            st,
        ),
        card(
            "Remaster ficou artificial",
            "Causa provável: filtro forte demais para o material original.\n"
            "Como resolver: use Remaster leve como ponto de partida e evite Remaster forte em vídeos com muito ruído.",
            st,
        ),
        card(
            "Processamento lento em arquivos grandes",
            "Causa provável: leitura e escrita no mesmo disco durante remuxagens ou modos inteligentes.\n"
            "Como resolver: em <b>Configurações &gt; Pastas de trabalho</b>, configure saída e temporários em discos diferentes quando possível.",
            st,
        ),
        card(
            "Capa errada em série",
            "Causa provável: o TMDb pode retornar capa geral, temporada incorreta ou resultado parecido.\n"
            "Como resolver: selecione a temporada correta, confira a prévia e só então aplique a capa.",
            st,
        ),
        card(
            "Player não exibe legenda",
            "Causa provável: alguns players lidam mal com determinados codecs, flags, anexos, capas ou ordem de faixas.\n"
            "Como resolver: teste em outro player, remova anexos problemáticos ou gere um novo MKV limpo.",
            st,
        ),
        card(
            "Bordas não detectadas automaticamente",
            "Causa provável: o vídeo tem telas pretas, logos ou variações que confundem a análise automática.\n"
            "Como resolver: use Corrigir Bordas em modo manual e informe os pixels a cortar em cima, baixo, esquerda ou direita.",
            st,
        ),
        p("Dicas de diagnóstico", st["section"]),
        *bullets([
            "Use Relatórios para listar áudio, legenda, codec, idioma e flags de todos os vídeos da pasta.",
            "Quando algo parecer errado, teste primeiro com um único arquivo antes de processar um lote inteiro.",
            "Para séries, mantenha episódios da mesma série e temporada na pasta quando for aplicar capa automática.",
            "Se um arquivo tiver muitas faixas extras, imagens ou anexos, use o editor de faixas antes da conversão.",
            "Para preservar o máximo de informações, prefira MKV. Para compatibilidade simples, use MP4.",
        ], st),
        p("Boas práticas", st["section"]),
        *bullets([
            "Mantenha uma cópia dos arquivos originais até conferir o resultado final.",
            "Use nomes de arquivos claros para melhorar buscas automáticas no TMDb.",
            "Confira a prévia da capa antes de aplicar em lote.",
            "Use o cache de capas como apoio, mas revise visualmente quando houver dúvida.",
            "Evite cancelar processos durante gravação se o arquivo de saída já estiver quase finalizado.",
        ], st),
        p("Contato", st["section"]),
        rich(
            "Caso ainda tenha dúvidas, entre em contato pelo e-mail <b>tecmabeinformatica@gmail.com</b>.",
            st["body"],
        ),
    ]
    build_pdf(OUT_HELP, "FFX Encoder GUI Ajuda", f"Ajuda - Versão {VERSION}", story)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    build_readme()
    build_help()
    print(OUT_README)
    print(OUT_HELP)


if __name__ == "__main__":
    main()

# FFX Encoder GUI - Projeto Portável

Este pacote foi separado para permitir manutenção futura do FFX Encoder GUI fora desta conversa ou em outra ferramenta de IA.

## Estrutura principal

- `gui_main.py`: interface gráfica principal do FFX Encoder GUI.
- `ffx_encoder/`: módulos auxiliares do projeto.
- `installer.iss`: instalador gráfico moderno compilado pelo Inno Setup 6.
- `FFX Encoder GUI.spec`: configuração do PyInstaller para gerar o aplicativo principal.
- `build_installer.ps1`: automatiza documentos, aplicativo e instalador final.
- `generate_final_docs.py`: gera os PDFs `Leia-me` e `Ajuda`.
- `bin/`: `ffmpeg.exe` e `ffprobe.exe` usados pelo app quando empacotado.
- `Documentos Corrigidos/`: PDFs corrigidos com acentuação normal.
- `release/`: instalador pronto da versão atual.

## Requisitos para editar e compilar

Instale Python 3.14 ou superior, [Inno Setup 6](https://jrsoftware.org/isdl.php) e depois:

```powershell
python -m pip install -r requirements-build.txt
```

## Gerar PDFs

```powershell
python generate_final_docs.py
```

Os PDFs corrigidos serão criados em:

```text
Documentos Corrigidos\
```

## Compilar o aplicativo principal

```powershell
python -m PyInstaller --noconfirm --clean "FFX Encoder GUI.spec"
```

O resultado principal será criado em:

```text
dist\FFX Encoder GUI\
```

## Compilar o instalador

```powershell
.\build_installer.ps1
```

O script gera os PDFs, compila o aplicativo com PyInstaller e cria o instalador
gráfico com o Inno Setup 6. O resultado é salvo em `release\`.

O instalador usa interface moderna e não abre uma janela de prompt. Ele também
cria o desinstalador nativo, oferece atalho na Área de Trabalho e instala o menu
de contexto opcional. A pasta pessoal `Capas` não é removida na desinstalação.

## Observações

- A pasta `Capas` instalada pelo usuário é cache/biblioteca pessoal e não deve ser apagada em atualizações.
- Para preservar compatibilidade, evite alterar funções já testadas sem criar uma build de teste separada.
- Antes de entregar uma versão, teste ao menos: abrir app, menu de contexto, TMDb, capas, metadados, editor de faixas, conversão, remaster, corrigir aspecto, corrigir bordas e modo inteligente.

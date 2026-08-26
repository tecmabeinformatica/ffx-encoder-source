# FFX Encoder GUI - Projeto Portável

Este pacote foi separado para permitir manutenção futura do FFX Encoder GUI fora desta conversa ou em outra ferramenta de IA.

## Estrutura principal

- `gui_main.py`: interface gráfica principal do FFX Encoder GUI.
- `ffx_encoder/`: módulos auxiliares do projeto.
- `InstallerBuildGUI/installer_gui.py`: instalador empacotado em Python.
- `FFX Encoder GUI.spec`: configuração do PyInstaller para gerar o aplicativo principal.
- `generate_final_docs.py`: gera os PDFs `Leia-me` e `Ajuda`.
- `bin/`: `ffmpeg.exe` e `ffprobe.exe` usados pelo app quando empacotado.
- `Documentos Corrigidos/`: PDFs corrigidos com acentuação normal.
- `release/`: instalador pronto da versão atual.

## Requisitos para editar e compilar

Instale Python 3.14 ou superior e depois:

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

## Atualizar o payload do instalador

Após compilar o app principal, copie para `dist\FFX Encoder GUI\`:

- `Desinstalar FFX Encoder GUI.bat`
- `Documentos Corrigidos\FFX Encoder GUI Leia-me.pdf`
- `Documentos Corrigidos\FFX Encoder GUI Ajuda.pdf`
- `FFX Encoder GUI Termo de Responsabilidade.pdf`
- `icone.ico`

Depois recrie:

```text
InstallerBuildGUI\FFX Encoder GUI Payload.zip
```

## Compilar o instalador

```powershell
python -m PyInstaller --noconfirm --clean --onefile --console --name "FFX Encoder GUI 2.0 Final Instalador" --icon "icone.ico" --add-data "InstallerBuildGUI\FFX Encoder GUI Payload.zip;." "InstallerBuildGUI\installer_gui.py"
```

## Observações

- A pasta `Capas` instalada pelo usuário é cache/biblioteca pessoal e não deve ser apagada em atualizações.
- Para preservar compatibilidade, evite alterar funções já testadas sem criar uma build de teste separada.
- Antes de entregar uma versão, teste ao menos: abrir app, menu de contexto, TMDb, capas, metadados, editor de faixas, conversão, remaster, corrigir aspecto, corrigir bordas e modo inteligente.

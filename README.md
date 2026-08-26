# FFX Encoder 3.0.0 Python

Base experimental da futura versao Python do FFX Encoder.

## Ideia

O FFmpeg continua sendo o motor principal. O Python fica responsavel por:

- menus;
- localizacao do FFmpeg e FFprobe;
- leitura dos arquivos da pasta;
- chamadas ao FFmpeg;
- logs e mensagens de erro;
- modulos separados para conversao, capas, metadados, audio e legendas.

## Compatibilidade com FFmpeg

Por enquanto a busca segue esta ordem:

1. `bin\ffmpeg.exe` e `bin\ffprobe.exe` ao lado da versao Python/EXE;
2. `C:\FFmpeg\bin\ffmpeg.exe` e `C:\FFmpeg\bin\ffprobe.exe`;
3. `ffmpeg.exe` e `ffprobe.exe` disponiveis no PATH do Windows.

Assim a versao final pode ser distribuida com o FFmpeg junto, sem depender da instalacao manual. Durante o desenvolvimento, ainda mantemos compatibilidade com sua instalacao atual em `C:\FFmpeg`.

Estrutura sugerida para distribuicao:

```text
FFX Encoder 3.0.0\
  FFX Encoder.exe
  bin\
    ffmpeg.exe
    ffprobe.exe
```

## Como testar em modo script

```powershell
python "D:\scripts\Projeto APP\FFX Encoder 3.0.0 Python\main.py"
```

Tambem e possivel informar a pasta de trabalho:

```powershell
python "D:\scripts\Projeto APP\FFX Encoder 3.0.0 Python\main.py" "E:\Testes"
```

## Menu de contexto experimental

Arquivos criados para teste:

- `install_context_menu_python.reg`
- `remove_context_menu_python.reg`
- `install_context_menu_python_silent.bat`
- `remove_context_menu_python_silent.bat`

Esse menu usa o nome `FFX Encoder 3.0.0 Python` para nao substituir a versao antiga.

## Cache de capas

A busca de capas em cache segue esta ordem:

1. `Capas` ao lado da versao Python/EXE;
2. `C:\FFmpeg\Capas`, para compatibilidade com o cache antigo.

Estrutura esperada:

```text
Capas\
  I Dream of Jeannie\
    Temporada 5.jpg
    Serie.jpg
```

## Estrutura inicial

- `main.py`: ponto de entrada.
- `ffx_encoder/config.py`: caminhos e configuracoes globais.
- `ffx_encoder/ffmpeg_tools.py`: localizacao e chamadas ao FFmpeg.
- `ffx_encoder/media.py`: listagem de arquivos de video e pastas de saida.
- `ffx_encoder/runner.py`: execucao do FFmpeg com spinner/progresso.
- `ffx_encoder/metadata.py`: funcoes de metadados.
- `ffx_encoder/menu.py`: menu principal.

## Progresso visual

- Funcoes sem recode usam spinner.
- Funcoes com recode deverao usar porcentagem quando forem migradas.
- Se a duracao nao puder ser detectada, a funcao pode voltar para spinner.

## Funcoes ja migradas

- `8 - Metadados > 1 - Limpar metadados`
- `8 - Metadados > 2 - Inserir metadados de filme (TMDb)`
- `7 - Capas > 1 - Aplicar capa local`
- `7 - Capas > 2 - Remover capas embutidas`
- `7 - Capas > 3 - Buscar capa no cache`
- `7 - Capas > 4 - Buscar capa no TMDb`
- `1 - Audio e Legendas > 1 - Manter apenas o audio 1`
- `1 - Audio e Legendas > 2 - Manter apenas o audio 2`
- `1 - Audio e Legendas > 3 - Manter apenas audio PT`
- `1 - Audio e Legendas > 4 - Manter PT+EN e legenda PT`
- `1 - Audio e Legendas > 5 - Juntar video + legenda externa`
- `1 - Audio e Legendas > 6 - Extrair audio`
- `1 - Audio e Legendas > 7 - Juntar audio externo`
- `2 - Converter`
- `3 - Upscale 1080p`
- `4 - Deinterlace`
- `5 - Denoise`
- `6 - Remaster`

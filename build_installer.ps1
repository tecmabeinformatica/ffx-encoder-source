$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$BuildPython = Join-Path $Root ".venv-build\Scripts\python.exe"
$Python = if (Test-Path -LiteralPath $BuildPython) { $BuildPython } else { "python" }
$AppName = "FFX Encoder GUI"
$InstallerName = "FFX Encoder GUI 2.1 Instalador"
$Dist = Join-Path $Root "dist\$AppName"
$Docs = Join-Path $Root "build\docs"
$InnoCompiler = Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"

if (-not (Test-Path -LiteralPath $InnoCompiler)) {
    throw "Inno Setup 6 não encontrado em: $InnoCompiler"
}

Write-Host "Gerando PDFs corrigidos..."
& $Python (Join-Path $Root "generate_final_docs.py")
if ($LASTEXITCODE -ne 0) {
    throw "A geração dos PDFs falhou. Consulte o erro exibido acima."
}

Write-Host "Compilando aplicativo principal..."
& $Python -m PyInstaller --noconfirm --clean (Join-Path $Root "FFX Encoder GUI.spec")
if ($LASTEXITCODE -ne 0) {
    throw "A compilação do aplicativo falhou. Consulte o erro exibido acima."
}

Write-Host "Adicionando documentos ao aplicativo..."
Copy-Item -LiteralPath (Join-Path $Docs "FFX Encoder GUI Leia-me.pdf") -Destination (Join-Path $Dist "FFX Encoder GUI Leia-me.pdf") -Force
Copy-Item -LiteralPath (Join-Path $Docs "FFX Encoder GUI Ajuda.pdf") -Destination (Join-Path $Dist "FFX Encoder GUI Ajuda.pdf") -Force
Copy-Item -LiteralPath (Join-Path $Root "FFX Encoder GUI Termo de Responsabilidade.pdf") -Destination $Dist -Force
Copy-Item -LiteralPath (Join-Path $Root "icone.ico") -Destination $Dist -Force

$Release = Join-Path $Root "release"
New-Item -ItemType Directory -Path $Release -Force | Out-Null

Write-Host "Compilando instalador gráfico com Inno Setup 6..."
& $InnoCompiler (Join-Path $Root "installer.iss")
if ($LASTEXITCODE -ne 0) {
    throw "O Inno Setup terminou com código $LASTEXITCODE."
}

Write-Host ""
Write-Host "[OK] Instalador criado em:"
Write-Host (Join-Path $Release "$InstallerName.exe")

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = "python"
$AppName = "FFX Encoder GUI"
$InstallerName = "FFX Encoder GUI 2.0 Final Instalador"
$Dist = Join-Path $Root "dist\$AppName"
$Docs = Join-Path $Root "Documentos Corrigidos"
$Payload = Join-Path $Root "InstallerBuildGUI\FFX Encoder GUI Payload.zip"

Write-Host "Gerando PDFs corrigidos..."
& $Python (Join-Path $Root "generate_final_docs.py")

Write-Host "Compilando aplicativo principal..."
& $Python -m PyInstaller --noconfirm --clean (Join-Path $Root "FFX Encoder GUI.spec")

Write-Host "Montando payload do instalador..."
Copy-Item -LiteralPath (Join-Path $Root "Desinstalar FFX Encoder GUI.bat") -Destination $Dist -Force
Copy-Item -LiteralPath (Join-Path $Docs "FFX Encoder GUI Leia-me.pdf") -Destination (Join-Path $Dist "FFX Encoder GUI Leia-me.pdf") -Force
Copy-Item -LiteralPath (Join-Path $Docs "FFX Encoder GUI Ajuda.pdf") -Destination (Join-Path $Dist "FFX Encoder GUI Ajuda.pdf") -Force
Copy-Item -LiteralPath (Join-Path $Root "FFX Encoder GUI Termo de Responsabilidade.pdf") -Destination $Dist -Force
Copy-Item -LiteralPath (Join-Path $Root "icone.ico") -Destination $Dist -Force

Remove-Item -LiteralPath $Payload -Force -ErrorAction SilentlyContinue
Compress-Archive -Path (Join-Path $Dist "*") -DestinationPath $Payload -CompressionLevel Optimal

Write-Host "Compilando instalador..."
& $Python -m PyInstaller --noconfirm --clean --onefile --console --name $InstallerName --icon (Join-Path $Root "icone.ico") --add-data "$Payload;." (Join-Path $Root "InstallerBuildGUI\installer_gui.py")

$Release = Join-Path $Root "release"
New-Item -ItemType Directory -Path $Release -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $Root "dist\$InstallerName.exe") -Destination (Join-Path $Release "$InstallerName.exe") -Force

Write-Host ""
Write-Host "[OK] Instalador criado em:"
Write-Host (Join-Path $Release "$InstallerName.exe")

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
python -m pip install pyinstaller
$uiPath = Join-Path $PSScriptRoot 'ui.html'
python -m PyInstaller --noconfirm --onefile --console --name TikTokPriceTool --add-data "$uiPath;." server.py
if ($LASTEXITCODE -ne 0) { throw 'Build TikTokPriceTool failed' }
python -m PyInstaller --noconfirm --onefile --console --name TikTokPricePublic --add-data "$uiPath;." public_server.py
if ($LASTEXITCODE -ne 0) { throw 'Build TikTokPricePublic failed' }

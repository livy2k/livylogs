# Build Script for LivyLogs
# Usage:
#   .\build.ps1        - Standard build (incremental, fast)
#   .\build.ps1 -Full  - Full build (clean, slower)
#   .\build.ps1 -Quick - Only update scripts/assets in existing dist (instant)

param (
    [switch]$Full,
    [switch]$Quick
)

$DistPath = "dist/LivyLogs"
$InternalPath = "$DistPath/_internal"

if ($Quick) {
    Write-Host ">>> performing QUICK update of scripts and assets..." -ForegroundColor Cyan
    if (Test-Path $DistPath) {
        # Copy updated python files to _internal (if using directory mode)
        # Note: PyInstaller bundles scripts into the executable or .pyc files.
        # For a truly quick update without rebuilding EXE, we mostly update non-compiled assets.
        # But usually, code changes require at least an incremental build.
        # We'll just copy the text configs and assets that users might change.
        Copy-Item "ui_labels_map.txt" $DistPath -Force
        Copy-Item "custom_stations.txt" $DistPath -Force
        Copy-Item "uimaker_bg.jpg" $DistPath -Force
        Write-Host ">>> Assets updated in $DistPath" -ForegroundColor Green
    } else {
        Write-Error "Distribution folder not found. Run a full build first."
    }
    exit
}

if ($Full) {
    Write-Host ">>> performing FULL clean build..." -ForegroundColor Yellow
    pyinstaller livylogs.spec --noconfirm --clean
} else {
    Write-Host ">>> performing INCREMENTAL build..." -ForegroundColor Cyan
    pyinstaller livylogs.spec --noconfirm
}

Write-Host ">>> Build Complete: $DistPath/LivyLogs.exe" -ForegroundColor Green

# Clean Python cache files and directories
Write-Host "Cleaning Python cache files..." -ForegroundColor Yellow

# Remove __pycache__ directories
$pycacheDirs = Get-ChildItem -Path . -Recurse -Directory -Filter __pycache__ -ErrorAction SilentlyContinue
if ($pycacheDirs) {
    Write-Host "Removing $($pycacheDirs.Count) __pycache__ directories..." -ForegroundColor Cyan
    $pycacheDirs | Remove-Item -Recurse -Force
} else {
    Write-Host "No __pycache__ directories found." -ForegroundColor Green
}

# Remove .pyc and .pyo files
$pycFiles = Get-ChildItem -Path . -Recurse -Include *.pyc,*.pyo -ErrorAction SilentlyContinue
if ($pycFiles) {
    Write-Host "Removing $($pycFiles.Count) .pyc/.pyo files..." -ForegroundColor Cyan
    $pycFiles | Remove-Item -Force
} else {
    Write-Host "No .pyc/.pyo files found." -ForegroundColor Green
}

# Remove .pytest_cache directories
$pytestCache = Get-ChildItem -Path . -Recurse -Directory -Filter .pytest_cache -ErrorAction SilentlyContinue
if ($pytestCache) {
    Write-Host "Removing $($pytestCache.Count) .pytest_cache directories..." -ForegroundColor Cyan
    $pytestCache | Remove-Item -Recurse -Force
} else {
    Write-Host "No .pytest_cache directories found." -ForegroundColor Green
}

# Remove .mypy_cache directories
$mypyCache = Get-ChildItem -Path . -Recurse -Directory -Filter .mypy_cache -ErrorAction SilentlyContinue
if ($mypyCache) {
    Write-Host "Removing $($mypyCache.Count) .mypy_cache directories..." -ForegroundColor Cyan
    $mypyCache | Remove-Item -Recurse -Force
} else {
    Write-Host "No .mypy_cache directories found." -ForegroundColor Green
}

Write-Host "`nCache cleanup complete!" -ForegroundColor Green

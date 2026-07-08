# Set output encoding to UTF-8 to prevent garbled characters
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "Running tests with verbose output via PowerShell..."
python -m unittest discover -v tests

# Real PowerShell parser; does not execute the target script.
# Wichtig: ParseFile liefert Fehler UNSORTIERT. Wir geben sie IMMER nach
# StartLine/StartColumn sortiert aus - sonst jagt man die falsche Zeile.
param([string]$Path = (Join-Path (Split-Path -Parent $PSScriptRoot) 'app\ArenaBridge.ps1'))
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
    Write-Output "PARSE-GATE: file missing: $Path"
    exit 1
}
$tokens = $null
$parseErrors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile(
    $Path, [ref]$tokens, [ref]$parseErrors)
$sorted = @($parseErrors) | Sort-Object { $_.Extent.StartLineNumber }, { $_.Extent.StartColumnNumber }
Write-Output ("PowerShell {0}; file: {1}; PARSE-FEHLER: {2}" -f $PSVersionTable.PSVersion, $Path, $sorted.Count)
foreach ($parseError in $sorted) {
    Write-Output ("{0}:{1}:{2}: {3} [{4}]" -f $Path,
        $parseError.Extent.StartLineNumber, $parseError.Extent.StartColumnNumber,
        $parseError.Message, $parseError.ErrorId)
}
if ($sorted.Count -gt 0) { exit 1 }
exit 0

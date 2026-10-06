# Real PowerShell parser; does not execute the target script.
param([string]$Path = (Join-Path $PSScriptRoot 'ArenaBridge.ps1'))
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
    Write-Output "PARSE-GATE: file missing: $Path"
    exit 1
}
$tokens = $null
$parseErrors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile(
    $Path, [ref]$tokens, [ref]$parseErrors)
Write-Output ("PowerShell {0}; file: {1}; PARSE-FEHLER: {2}" -f $PSVersionTable.PSVersion, $Path, $parseErrors.Count)
foreach ($parseError in $parseErrors) {
    Write-Output ("{0}:{1}:{2}: {3} [{4}]" -f $Path,
        $parseError.Extent.StartLineNumber, $parseError.Extent.StartColumnNumber,
        $parseError.Message, $parseError.ErrorId)
}
if ($parseErrors.Count -gt 0) { exit 1 }
exit 0

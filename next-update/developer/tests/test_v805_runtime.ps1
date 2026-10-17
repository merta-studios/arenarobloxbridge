# Run with Windows PowerShell 5.1. Loads only selected function ASTs; no GUI,
# server, Roblox, real desktop entries or external APIs are started. The
# shortcut test uses a throw-away folder under %TEMP% and a dummy EXE file.
$ErrorActionPreference = 'Stop'
$sourcePath = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) 'app\ArenaBridge.ps1'
$tokens = $null; $errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($sourcePath, [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
function Load-Function([string]$Name) {
    $node = $ast.Find({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $Name }, $true)
    if (-not $node) { throw "Missing function $Name" }
    return [scriptblock]::Create($node.Extent.Text)
}
foreach ($name in @('Test-ArenaBridgeShortcutTarget', 'Get-ArenaShortcutInfo', 'Initialize-ArenaDesktopShortcut')) {
    . (Load-Function $name)
}
function Assert([bool]$Condition, [string]$Label) {
    if (-not $Condition) { throw "FAILED: $Label" }
    Write-Output "OK: $Label"
}

$source = [System.IO.File]::ReadAllText($sourcePath)

# 1) Tool catalogs: every 8.0.5 tool has docs, a label and an activity text.
$newTools = @('terrain_heightmap', 'terrain_sculpt', 'terrain_paint', 'terrain_water',
    'terrain_feature', 'terrain_carve', 'terrain_measure', 'terrain_clear',
    'camera_state', 'camera_reset', 'camera_focus', 'camera_guard', 'ui_widget')
$activityStart = $source.IndexOf('function Get-ArenaActivityText')
$activityEnd = $source.IndexOf('function Get-ArenaActivityKind', $activityStart)
Assert ($activityStart -ge 0 -and $activityEnd -gt $activityStart) 'activity text block found'
$activity = $source.Substring($activityStart, $activityEnd - $activityStart)
foreach ($tool in $newTools) {
    Assert ($source.Contains("name = '$tool'")) "tool docs contain $tool"
    Assert ([regex]::IsMatch($source, "(?m)^        $tool = '")) "activity label contains $tool"
    Assert ([regex]::IsMatch($activity, "(?m)^            $tool = '")) "activity text contains $tool"
}

# 2) The plugin ships all 40 UI styles and the widget library.
$luaStart = $source.IndexOf("function Get-PluginSource {")
$luaEnd = $source.IndexOf("`n'@`n}", $luaStart)
Assert ($luaStart -ge 0 -and $luaEnd -gt $luaStart) 'plugin source block found'
$plugin = $source.Substring($luaStart, $luaEnd - $luaStart)
$skinsStart = $plugin.IndexOf('UI_ENGINE.SKINS = {')
$skinsEnd = $plugin.IndexOf('function UI_ENGINE.skinNames()', $skinsStart)
Assert ($skinsStart -ge 0 -and $skinsEnd -gt $skinsStart) 'skin table found'
$skinCount = [regex]::Matches($plugin.Substring($skinsStart, $skinsEnd - $skinsStart), "(?m)^\s{4}[a-z][a-z0-9]* = \{ label = ").Count
Assert ($skinCount -ge 40) "at least 40 UI styles in the plugin ($skinCount)"
Assert ($plugin.Contains('UI_ENGINE.WIDGETS = {')) 'widget library present'
Assert ($plugin.Contains('UI_ENGINE.outlineLayer') -and $plugin.Contains('UI_ENGINE.glossLayer') -and
        $plugin.Contains('UI_ENGINE.decorLayer')) 'outline, gloss and decor layers present'

# 3) Shortcut allow-list never accepts foreign programs.
Assert (Test-ArenaBridgeShortcutTarget 'C:\Apps\ArenaRobloxBridge.exe') 'ArenaRobloxBridge.exe accepted'
Assert (Test-ArenaBridgeShortcutTarget 'C:\Apps\ArenaBridge-7.6.3.exe') 'ArenaBridge-7.6.3.exe accepted'
Assert (-not (Test-ArenaBridgeShortcutTarget 'C:\Windows\notepad.exe')) 'notepad.exe rejected'
Assert (-not (Test-ArenaBridgeShortcutTarget '')) 'empty target rejected'

# 4) Script mode must not touch the desktop at all.
$script:IsExeMode = $false
$script:RuntimeLog = Join-Path $env:TEMP 'arena-v805-runtime.log'
function Write-RuntimeLog([string]$Message) { }
$script:MockExe = ''
$script:MockDesktop = ''
function Get-ArenaOwnExePath { return $script:MockExe }
function Get-ArenaDesktopFolder { return $script:MockDesktop }
$skipped = Initialize-ArenaDesktopShortcut
Assert ($skipped.state -eq 'skipped' -and $skipped.reason -eq 'script-mode') 'script mode skips the shortcut'

# 5) EXE mode creates, keeps and repairs the shortcut in a temp folder.
$tempRoot = Join-Path $env:TEMP ('arena-v805-shortcut-' + [Guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $tempRoot
try {
    $exe = Join-Path $tempRoot 'ArenaRobloxBridge.exe'
    Set-Content -LiteralPath $exe -Value 'dummy' -Encoding ASCII
    $script:IsExeMode = $true
    $script:MockExe = $exe
    $script:MockDesktop = $tempRoot
    $canonical = Join-Path $tempRoot 'Arena Roblox Bridge.lnk'

    $first = Initialize-ArenaDesktopShortcut
    Assert ($first.state -eq 'ok' -and $first.created -and (Test-Path -LiteralPath $canonical)) 'shortcut created'

    $second = Initialize-ArenaDesktopShortcut
    Assert ($second.state -eq 'ok' -and $second.reason -eq 'already-current') 'current shortcut is left alone'

    Remove-Item -LiteralPath $canonical -Force
    $third = Initialize-ArenaDesktopShortcut
    Assert ($third.state -eq 'ok' -and $third.created) 'deleted shortcut is recreated'

    $foreign = Join-Path $tempRoot 'ArenaBridge.lnk'
    $shell = New-Object -ComObject WScript.Shell
    $link = $shell.CreateShortcut($foreign)
    $link.TargetPath = (Join-Path $env:WINDIR 'notepad.exe')
    $link.Save()
    $null = Initialize-ArenaDesktopShortcut
    Assert (Test-Path -LiteralPath $foreign) 'foreign program shortcut is never deleted'
} finally {
    Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Output 'OK: 8.0.5 runtime contracts (tools, skins, shortcut lifecycle) passed.'

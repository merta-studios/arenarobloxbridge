# Run with Windows PowerShell 5.1. Loads only selected function ASTs; no GUI,
# server, Roblox, real registry entries or external APIs are started.
$ErrorActionPreference = 'Stop'
$sourcePath = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) 'app\ArenaBridge.ps1'
$tokens=$null; $errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile($sourcePath,[ref]$tokens,[ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
function Load-Function([string]$Name) {
    $node=$ast.Find({param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $Name},$true)
    if (-not $node) { throw "Missing function $Name" }
    return [scriptblock]::Create($node.Extent.Text)
}
foreach ($name in @('Get-NormalizedPlaceName','Test-StandardPlaceName','Get-PlaceNameQuality','Save-PlaceName',
    'Get-PlaceIdentity','Save-PlaceIdentity','Get-PlaceIdentityKey','Resolve-PlaceWindowIdentity','Test-PreviewHandleClaimed',
    'Resolve-OpenCloudCreatorForUpload','Grant-SessionAssetUse','Resolve-BridgeUpdaterExePath','Get-StartupEnabled',
    'Get-UiDisplayText','Get-LocalizedXamlText','Get-UiLanguage')) { . (Load-Function $name) }
function Assert([bool]$Condition,[string]$Label) { if (-not $Condition) { throw "FAILED: $Label" }; Write-Output "OK: $Label" }
function Repair-Mojibake([string]$Text) { return $Text }
$script:Shared=@{
    Sessions=[System.Collections.Concurrent.ConcurrentDictionary[string,string]]::new()
    Presence=[System.Collections.Concurrent.ConcurrentDictionary[string,long]]::new()
    StudioCaptureTargets=[System.Collections.Concurrent.ConcurrentDictionary[string,string]]::new()
}
$script:PlaceIdentities=@{}; $script:PlaceNames=@{}; $script:PlaceNameSources=@{}; $script:PreviewHandleClaims=@{}
$script:MockInfos=@()
function Get-StudioWindowInfos { return $script:MockInfos }
function Session([string]$Id,[string]$Name) {
    $s=@{sessionId=$Id;instanceGuid=$Id;placeName=$Name;placeId='123';lastSeen=[DateTimeOffset]::UtcNow.ToUnixTimeSeconds();editorUserId='101';creatorId='303';creatorType='User';gameId='202'}
    $script:Shared.Sessions[$Id]=$s|ConvertTo-Json -Compress
    return $s
}
$a=Session 'a' 'Egg Game'; $b=Session 'b' 'Other Game'
$script:MockInfos=@([pscustomobject]@{Handle=[IntPtr]12;ProcessId=102;Title='Other Game - Local Script'},[pscustomobject]@{Handle=[IntPtr]11;ProcessId=101;Title='Egg Game'})
$ia=Resolve-PlaceWindowIdentity $a 'a'; $ib=Resolve-PlaceWindowIdentity $b 'b'
Assert ($ia.ProcessId -eq 101 -and $ib.ProcessId -eq 102) 'two sessions bind to their own windows despite reversed enumeration'
$script:MockInfos=@($script:MockInfos[0])
$ia=Resolve-PlaceWindowIdentity $a 'a'; $ib=Resolve-PlaceWindowIdentity $b 'b'
Assert ($ia.WindowHandle -eq [IntPtr]::Zero -and $ib.WindowHandle -eq [IntPtr]12) 'closing A never gives B the name or preview of A'
Assert (-not $script:Shared.StudioCaptureTargets.ContainsKey('a')) 'closed window capture target removed'
Assert ((Get-NormalizedPlaceName 'Egg Game - Local Script - Roblox Studio') -eq 'Egg Game') 'script suffix removed'
Assert ((Get-NormalizedPlaceName 'Place4') -eq '') 'placeholder rejected'
$c=Session 'c' 'Same'; $d=Session 'd' 'Same'
$script:MockInfos=@([pscustomobject]@{Handle=[IntPtr]13;ProcessId=103;Title='Same'},[pscustomobject]@{Handle=[IntPtr]14;ProcessId=104;Title='Same'})
Assert ((Resolve-PlaceWindowIdentity $c 'c').WindowHandle -eq [IntPtr]::Zero) 'ambiguous titles fail closed'
[void](Save-PlaceName 'a' 'Published name' 'plugin')
[void](Save-PlaceName 'a' 'Wrong window' 'windowTitle')
Assert ($script:PlaceNames.a -eq 'Published name') 'published/plugin name outranks title'

function Get-SessionEntry($id) { return ($script:Shared.Sessions[$id] | ConvertFrom-Json) }
function Get-OpenCloudStudioDeveloper { return @{ok=$true;creatorKind='user';creatorId='101'} }
function Resolve-OpenCloudCreatorFromKey { return @{ok=$true;creatorKind='user';creatorId='999'} }
$group=Session 'g' 'Group Place'; $group.creatorType='Group'; $group.creatorId='303'; $script:Shared.Sessions['g']=$group|ConvertTo-Json -Compress
$owner=Resolve-OpenCloudCreatorForUpload -Shared $script:Shared -SessionId 'g'
Assert ($owner.creatorKind -eq 'group' -and $owner.creatorId -eq '303') 'group owner wins over signed-in account and key fallback'
$owner=Resolve-OpenCloudCreatorForUpload -Shared $script:Shared -SessionId 'a'
Assert ($owner.creatorKind -eq 'user' -and $owner.creatorId -eq '101') 'personal-place upload still uses studio account'
$script:CloudArgs=$null; $script:CloudAllowed=$true
function Invoke-OpenCloudCatalogTool($Shared,$SessionId,$Arguments) { $script:CloudArgs=$Arguments; return @{ok=$script:CloudAllowed;code='MOCK_DENIED'} }
$grant=Grant-SessionAssetUse -SessionId 'g' -AssetId '505'
Assert ($grant.ok -and $script:CloudArgs.operation -eq 'patch__asset_permissions_api_v1_assets_permissions') 'grant uses reviewed catalog API-key operation'
Assert ($script:CloudArgs.body.subjectType -eq 'Universe' -and $script:CloudArgs.body.subjectId -eq '202' -and $script:CloudArgs.body.action -eq 'Use') 'grant targets only this universe and Use (not All, Edit or ownership)'
$script:CloudAllowed=$false
Assert (-not (Grant-SessionAssetUse -SessionId 'g' -AssetId '505').ok) 'catalog access refusal is preserved'

# Resolve the running executable before any old preferred/startup/cached path.
$script:IsExeMode=$true; $script:ExePath='C:\New\ArenaRobloxBridge (1).exe'
$script:AppRoot='C:\New';$script:RepoRoot='C:\New';$script:AppDataRoot='C:\Data';$script:BinFolder='C:\Data\bin';$script:UpdaterPathFile='C:\Data\path.txt'
$script:UpdaterExePath='C:\Old\ArenaBridge.exe'
function Get-BridgeStartupItems { return ,@([pscustomobject]@{kind='registry';value='C:\Old\ArenaBridge.exe'}) }
function Get-BridgeUpdaterPathFromParent { return $null }
function Test-BridgeUpdaterExecutable($Path) { if ($Path -like '*.exe') { return $Path } }
function Get-BridgeUpdaterPathFromCommandLine { return $null }
function Test-Path { return $false }
function Get-CimInstance { return @() }
function Set-StartupEnabled($Enabled,$UpdaterPath) { $script:InstalledStartup=$UpdaterPath; return $true }
[void](Get-StartupEnabled)
Assert ($script:InstalledStartup -eq $script:ExePath) 'startup migrated to current EXE, not old preferred path'

# UI catalog and one-pass localization (no WPF dependency here).
$catalogPath=Join-Path (Split-Path -Parent $sourcePath) 'localization\en.json'
$script:UiTranslationsDeEn=@{}
foreach ($property in (Get-Content -Raw -Encoding UTF8 $catalogPath | ConvertFrom-Json).PSObject.Properties) { $script:UiTranslationsDeEn[$property.Name]=[string]$property.Value }
foreach ($variable in @('$script:UiTranslationPattern','$script:UiTranslationRegex')) {
    $assignment=$ast.Find({param($n) $n -is [System.Management.Automation.Language.AssignmentStatementAst] -and $n.Left.Extent.Text -eq $variable},$true)
    if (-not $assignment) { throw "Missing translation assignment $variable" }
    . ([scriptblock]::Create($assignment.Extent.Text))
}
$script:UiLanguage='en'
Assert ((Get-UiDisplayText 'Seit über einer Minute kein Bridge-Aufruf') -eq 'No Bridge request for over a minute') 'activity status translated'
$xaml=Get-LocalizedXamlText '<TextBlock Name="Einstellungen" Text="Einstellungen"/>'
Assert ($xaml -eq '<TextBlock Name="Einstellungen" Text="Settings"/>') 'XAML names untouched, display text translated'
Assert ((Get-UiDisplayText 'Hat „Einstellungen“ geprüft.') -match '„Einstellungen“') 'quoted user data is not translated'
Assert ((Get-UiDisplayText 'Geändert: Elsewhere') -notmatch 'Elsewherewhere') 'fragments are not cascaded'
Assert (-not (Grant-SessionAssetUse -SessionId 'g' -AssetId '9999999999999999999').ok) 'overflow asset ID fails safely'
$script:UiLanguage='de'
Assert ((Get-UiDisplayText 'Einstellungen') -eq 'Einstellungen') 'German source remains unchanged'
Write-Output '8.0.3 function runtime checks passed. Real WPF, desktop capture and Roblox live tests remain separate.'

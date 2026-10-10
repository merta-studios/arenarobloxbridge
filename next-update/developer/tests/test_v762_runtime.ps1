# Run on Windows PowerShell 5.1: powershell -NoProfile -File test_v762_runtime.ps1
# Loads ONLY the Open Cloud function block. No UI, startup, key files or network.
$ErrorActionPreference = 'Stop'
$tokens = $null; $errors = $null
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$sourcePath = Join-Path (Join-Path $projectRoot 'app') 'ArenaBridge.ps1'
$ast = [System.Management.Automation.Language.Parser]::ParseFile($sourcePath, [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
$block = $ast.Find({
    param($node)
    return ($node -is [System.Management.Automation.Language.ScriptBlockExpressionAst] -and $node.Extent.Text.Contains('# BEGIN GENERATED OPEN CLOUD CATALOG'))
}, $true)
if ($null -eq $block) { throw 'Open Cloud function block not found' }
. ($block.ScriptBlock.GetScriptBlock())
function Assert($condition, $message) { if (-not $condition) { throw $message }; Write-Output "OK: $message" }
$script:Fixture = @{ name='all'; enabled=$true; expired=$false; expirationTimeUtc=$null; scopes=@() }
foreach ($property in (Get-OpenCloudCatalog).permissions.PSObject.Properties) {
    $pair = $property.Name.Split(':')
    $script:Fixture.scopes += @{ name=$pair[0]; operations=@($pair[1]); universeIds=@('123') }
}
$script:Fixture.scopes += @{ name='asset-permissions'; operations=@('write') }
$script:Fixture.scopes += @{ name='universe.analytics.alert'; operations=@('read','write') }
$script:Fixture.scopes += @{ name='memory-store'; operations=@('flush') }
$script:Fixture.scopes += @{ name='unknown-future'; operations=@('read') }
$script:Secret = 'TEST-ONLY-NOT-A-REAL-KEY'
function Get-OpenCloudConfig { param($Shared); return @{hasKey=$true; key=$script:Secret} }
$script:OriginalSend = ${function:Send-OpenCloudHttp}
$script:Broken = $false
function Send-OpenCloudHttp {
    param($Shared,$Method,$Url,$Key,$JsonBody,$TimeoutSeconds,[int]$MaxResponseChars=600)
    if ($script:Broken) { return @{status=0; error='offline'; transport='mock'} }
    $json = ConvertTo-Json -InputObject $script:Fixture -Depth 15 -Compress
    Assert ($MaxResponseChars -gt $json.Length) 'introspection is not clipped to 600 characters' | Out-Null
    return @{status=200; body=$json; transport='mock'; bodyTruncated=$false}
}
$shared = @{ OpenCloudIntrospectCache=$null; AccessModes=[System.Collections.Concurrent.ConcurrentDictionary[string,string]]::new() }
$shared.AccessModes['test'] = 'readwrite'
$info = Invoke-OpenCloudIntrospect -Shared $shared
Assert ($info.ok) 'all-permission key introspects successfully'
foreach ($permission in (Get-OpenCloudCatalog).permissions.PSObject.Properties.Name) {
    Assert (Test-OpenCloudPermission $info $permission) "exact granted permission: $permission"
}
Assert (-not (Test-OpenCloudPermission $info 'memory-store:flush')) 'blocked scopes remain unusable'
$onlyRead = @{scopes=@(@{name='asset';operations=@('read')})}
Assert (Test-OpenCloudPermission $onlyRead 'asset:read') 'read-only asset permission accepted'
Assert (-not (Test-OpenCloudPermission $onlyRead 'asset:write')) 'read does not imply write'
$collision = @{scopes=@(@{name='asset-permissions';operations=@('write')},@{name='universe.analytics.alert';operations=@('read')})}
Assert (-not (Test-OpenCloudPermission $collision 'asset:write')) 'asset-permissions does not imply asset write'
Assert (-not (Test-OpenCloudPermission $collision 'universe.analytics:read')) 'analytics alerts do not imply analytics read'
$flat = @{scopes=@(@{name='ASSET:READ';operations=@()})}
Assert (Test-OpenCloudPermission $flat 'asset:read') 'flat colon-form permission is normalized'
$listOnly = @{scopes=@(@{name='universe-datastores.objects';operations=@('list')})}
Assert (-not (Test-OpenCloudPermission $listOnly 'universe-datastores.objects:read')) 'list does not imply read'
$readInfo=@{ok=$true;enabled=$true;scopes=$onlyRead.scopes}
Set-OpenCloudIntrospectCache $shared $readInfo
Assert ((Assert-OpenCloudToolAccess $shared -RequiredScopes @('asset:read')).ok) 'read-only key passes a read gate'
Assert ((Assert-OpenCloudToolAccess $shared -RequiredScopes @('asset:write')).code -eq 'OPENCLOUD_SCOPE_INCOMPLETE') 'missing write scope blocks'
$readInfo.hasExpiration=$true
Set-OpenCloudIntrospectCache $shared $readInfo
Assert ((Assert-OpenCloudToolAccess $shared -RequiredScopes @('asset:read')).code -eq 'OPENCLOUD_KEY_HAS_EXPIRATION') 'expiration blocks'
$readInfo.hasExpiration=$false; $readInfo.enabled=$false
Set-OpenCloudIntrospectCache $shared $readInfo
Assert ((Assert-OpenCloudToolAccess $shared -RequiredScopes @('asset:read')).code -eq 'OPENCLOUD_KEY_REJECTED') 'disabled key blocks'
$shared.OpenCloudIntrospectCache=$null
$script:Broken=$true
Assert ((Assert-OpenCloudToolAccess $shared -RequiredScopes @('asset:read')).code -eq 'OPENCLOUD_CHECK_FAILED') 'failed introspection is fail-closed'
$script:Broken=$false
Set-OpenCloudIntrospectCache $shared $info
$script:Sends=0; $script:LastRequest=$null
function Send-OpenCloudRequestFallback {
    param($Method,$Url,$Key,$MultipartBytes,$MultipartContentType,$AdditionalHeaders,$TimeoutSeconds,$MaxResponseChars)
    $script:Sends++
    $script:LastRequest=@{method=$Method;url=$Url;contentType=$MultipartContentType;bytes=$MultipartBytes;headers=$AdditionalHeaders}
    return @{status=200; body=('{"echo":"'+$Key+'"}'); bodyTruncated=$false; error=''}
}
$r=Invoke-OpenCloudCatalogTool $shared 'test' @{action='call';operation='not-allowed';url='https://evil.invalid'}
Assert ($r.code -eq 'OPENCLOUD_POLICY_DENIED' -and $script:Sends -eq 0) 'unknown operations never send'
$shared.AccessModes['test']='readonly'
$r=Invoke-OpenCloudCatalogTool $shared 'test' @{action='call';operation='Places_CreatePlaceVersionApiKey'}
Assert ($r.code -eq 'READONLY_TOKEN' -and $script:Sends -eq 0) 'read-only publishing never sends'
$shared.AccessModes['test']='readwrite'
$r=Invoke-OpenCloudCatalogTool $shared 'test' @{action='call';operation='Cloud_GetUniverse';path=@{universe_id='..'}}
Assert ($r.code -eq 'BAD_ARGS' -and $script:Sends -eq 0) 'path traversal never sends'
$r=Invoke-OpenCloudCatalogTool $shared 'test' @{action='call';operation='Cloud_GetUniverse';path=@{universe_id='123'};headers=@{'x-api-key'='override'}}
Assert ($r.code -eq 'BAD_ARGS' -and $script:Sends -eq 0) 'auth header override never sends'
$bytes=[Text.Encoding]::UTF8.GetBytes('<roblox/>')
$r=Invoke-OpenCloudCatalogTool $shared 'test' @{action='call';operation='Places_CreatePlaceVersionApiKey';path=@{universeId='123';placeId='456'};query=@{versionType='Published'};contentBase64=[Convert]::ToBase64String($bytes);contentType='application/xml'}
Assert ($r.ok -and $script:Sends -eq 1) 'publish sends exactly once'
Assert ($script:LastRequest.url -eq 'https://apis.roblox.com/universes/v1/123/places/456/versions?versionType=Published') 'publish URL is fixed and encoded'
Assert ([Text.Encoding]::UTF8.GetString($script:LastRequest.bytes) -eq '<roblox/>') 'publish is raw binary, not JSON or multipart'
Assert (($r | ConvertTo-Json -Depth 10) -notmatch [regex]::Escape($script:Secret)) 'API response cannot echo the key'
$asset=@((Get-OpenCloudCatalog).operations | Where-Object {$_.id -eq 'Assets_CreateAsset'})[0]
$body=New-OpenCloudCatalogBody $asset @{form=@{request=@{assetType='Audio';displayName='Test'}};files=@(@{field='fileContent';fileName='test.wav';contentType='audio/wav';contentBase64=[Convert]::ToBase64String([byte[]]@(1,2,3))})}
Assert ($body.contentType.StartsWith('multipart/form-data; boundary=')) 'multipart content type has boundary'
$text=[Text.Encoding]::UTF8.GetString($body.bytes)
Assert ($text.Contains('name="request"') -and $text.Contains('name="fileContent"') -and $text.Contains('audio/wav')) 'multipart preserves metadata and file parts'
foreach ($extension in @('mp3','ogg','wav','flac','rbxm','rbxmx','mp4','mov')) {
    Assert ((Get-OpenCloudAssetSpec ('test.'+$extension)).ok) "upload format $extension"
}
Assert ((Get-OpenCloudAssetSpec 'test.rbxm' 'Animation').assetType -eq 'Animation') 'animation type is explicit'
Assert (-not (Get-OpenCloudAssetSpec 'test.wav' 'Model').ok) 'incompatible type rejected'
Write-Output 'PASS: mocked PowerShell Open Cloud runtime tests (no live network).'

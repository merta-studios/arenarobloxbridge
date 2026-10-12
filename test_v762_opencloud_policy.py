#!/usr/bin/env python3
"""Offline tests of the shipped policy/schema and PS wiring (not Windows execution)."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT/'ArenaBridge.ps1').read_text(encoding='utf-8-sig')
CAT = json.loads((ROOT/'opencloud/catalog.json').read_text())
PERMISSIONS = json.loads((ROOT/'opencloud/permissions.json').read_text())
DENIED = '''thumbnail:read user.advanced:read user.social:read
universe.user-restriction:write universe.place.instance:read universe.place.instance:write
universe.analytics.alert:read universe.analytics.alert:write
universe.subscription-product.subscription:read studio-evaluations:create
universe.secret:read universe.secret:write user.user-notification:write
universe-messaging-service:publish memory-store:get memory-store:flush
memory-store.sorted-map:write memory-store.sorted-map:read memory-store.queue:add
memory-store.queue:dequeue memory-store.queue:discard
universe.place.luau-execution-session:read universe.place.luau-execution-session:write
legacy-user:manage legacy-team-collaboration:manage legacy-group:manage
legacy-universe.following:read legacy-universe.following:write
legacy-universe.badge:manage-and-spend-robux legacy-asset:manage
legacy-badge:manage group:read group:write group-forum:read group-forum:write
ad.billing:read ad.campaign:read ad.campaign:write'''.split()

def function(name, following):
    return SOURCE.split('    function '+name+' {',1)[1].split('    function '+following+' {',1)[0]

class CloudPolicy(unittest.TestCase):
    def test_exact_user_allowlist(self):
        expected = set('''asset:read asset:write developer-product:read developer-product:write
        game-pass:read game-pass:write universe.place:read universe.place:write universe:read universe:write
        universe-datastores.objects:read universe-datastores.objects:create universe-datastores.objects:update
        universe-datastores.objects:delete universe-datastores.objects:list
        universe-datastores.versions:read universe-datastores.versions:list
        universe-datastores.control:create universe-datastores.control:delete universe-datastores.control:list
        universe-datastores.control:snapshot universe-places:write universe.analytics:read universe.analytics:write
        universe.user-restriction:read universe.thumbnail:read universe.thumbnail:write universe.event:read
        universe.event:write universe.ordered-data-store.scope.entry:read universe.ordered-data-store.scope.entry:write
        creator-store-save:read creator-store-save:write legacy-universe:manage legacy-game-pass:manage
        legacy-developer-product:manage legacy-universe.badge:write user.inventory-item:read
        creator-store-product:read creator-store-product:write asset-permissions:write'''.split())
        self.assertEqual(set(PERMISSIONS), expected)
        self.assertEqual(len(expected),41)
        self.assertFalse(expected.intersection(DENIED))

    def test_embedded_catalog_matches_reviewed_source(self):
        embedded = SOURCE.split('# BEGIN GENERATED OPEN CLOUD CATALOG',1)[1].split("@'\n",1)[1].split("\n'@",1)[0]
        self.assertEqual(json.loads(embedded), CAT)
        self.assertEqual(CAT['permissions'],PERMISSIONS)
        self.assertEqual(len(CAT['operations']),172)
        self.assertEqual(len({o['id'] for o in CAT['operations']}),172)

    def test_no_denied_operation_or_scope_in_catalog(self):
        for op in CAT['operations']:
            self.assertTrue(set(op['policyScopes']) <= PERMISSIONS.keys(),op['id'])
            self.assertTrue(set(op['scopes']) <= PERMISSIONS.keys(),op['id'])
            self.assertTrue(op['path'].startswith('/'))
            self.assertNotIn('subscription',op['path'])
            self.assertNotIn('/instances/',op['path'])
            self.assertNotIn('luau-execution',op['path'])
            self.assertNotIn('/secrets',op['path'])
            self.assertNotIn('analytics-alert',op['path'])
        badges=[o for o in CAT['operations'] if o['path'].startswith('/legacy-badges/')]
        self.assertEqual([(o['method'],o['path'],o['scopes']) for o in badges],
                         [('PATCH','/legacy-badges/v1/badges/{badgeId}',['legacy-universe.badge:write'])])
        restrictions=[o for o in CAT['operations'] if 'universe.user-restriction:read' in o['scopes']]
        self.assertTrue(restrictions)
        self.assertTrue(all(o['method']=='GET' for o in restrictions))

    def test_coverage_no_invented_analytics_write(self):
        covered={s for o in CAT['operations'] for s in o['policyScopes']}
        self.assertEqual(set(PERMISSIONS)-covered,{'universe.analytics:write'})
        self.assertIn('kein API-Key-Endpunkt',PERMISSIONS['universe.analytics:write'])
        for word in ['Audio','Animationen','Videos','Metadaten','Versionen']:
            self.assertIn(word,PERMISSIONS['asset:write'])
        for o in CAT['operations']:
            self.assertTrue(o['documentation'].startswith('https://create.roblox.com/docs/'),o['id'])

    def test_complete_request_schema_refs_and_path_params(self):
        for op in CAT['operations']:
            def refs(v):
                if isinstance(v,dict):
                    if '$ref' in v:
                        name=v['$ref'].removeprefix('#/components/schemas/')
                        self.assertIn(name,op['components']['schemas'],op['id'])
                    for w in v.values(): refs(w)
                elif isinstance(v,list):
                    for w in v:refs(w)
            refs(op)
            paths={p['name'] for p in op['parameters'] if p['in']=='path'}
            self.assertEqual(set(re.findall(r'\{([^}]+)\}',op['path'])),paths)

    def test_large_introspection_regression_fixture(self):
        # Demonstrate the old 600-char truncation bug independently of Roblox.
        scopes=[{'name':p.rsplit(':',1)[0],'operations':[p.rsplit(':',1)[1]],'universeIds':['123']} for p in list(PERMISSIONS)+DENIED]
        for fixture in [{'name':'assets only','enabled':True,'scopes':scopes[:2]},
                        {'name':'all rights','enabled':True,'scopes':scopes},
                        {'name':'unknown extra','enabled':True,'scopes':scopes+[{'name':'future','operations':['new']}]}]:
            payload=json.dumps(fixture,ensure_ascii=False)
            self.assertLess(len(payload),2000000)
            self.assertEqual(json.loads(payload),fixture)
            if len(payload)>600:
                with self.assertRaises(json.JSONDecodeError):json.loads(payload[:600])
        intro=function('Invoke-OpenCloudIntrospect','Get-OpenCloudArgumentValue')
        self.assertIn('-MaxResponseChars 2000000',intro)
        self.assertIn('if ($attempt.bodyTruncated)',intro)
        self.assertIn('OPENCLOUD_RESPONSE_TOO_LARGE',intro)
        self.assertIn("$scopeBase -eq 'asset'",intro)
        self.assertNotIn("$scopeBase.Contains('asset')",intro)
        http=function('Send-OpenCloudHttp','Get-OpenCloudTransportError')
        self.assertIn('$out.bodyTruncated = $text.Length -gt $responseLimit',http)
        self.assertIn('$out.bodyTruncated = [bool]$fallback.bodyTruncated',http)

    def test_exact_gate_and_fail_closed(self):
        exact=function('Test-OpenCloudPermission','Assert-OpenCloudToolAccess')
        self.assertIn('-ceq $wanted',exact)
        self.assertNotIn('.StartsWith(',exact)
        gate=function('Assert-OpenCloudToolAccess','ConvertTo-OpenCloudMap')
        for marker in ['OPENCLOUD_CHECK_FAILED','OPENCLOUD_KEY_HAS_EXPIRATION','OPENCLOUD_KEY_REJECTED','OPENCLOUD_SCOPE_INCOMPLETE','OPENCLOUD_POLICY_DENIED','Test-OpenCloudPermission']:
            self.assertIn(marker,gate)
        self.assertNotIn('Get-OpenCloudFamilyCoverage',SOURCE)
        self.assertIn('-RequiredScopes $RequiredScopes',function('Invoke-CreatorDashboardHttp','Invoke-CreatorDashboardTool'))
        self.assertIn('-RequiredScopes $RequiredScopes',function('Invoke-DatastoreHttp','Invoke-DatastoreTool'))

    def test_dispatcher_no_proxy_no_local_files(self):
        tool=function('Invoke-OpenCloudCatalogTool','Get-OpenCloudAssetSpec')
        self.assertIn("$_.id -ceq [string]$Arguments.operation",tool)
        self.assertIn("$url = 'https://apis.roblox.com' + $path",tool)
        self.assertNotIn('$Arguments.url',tool)
        self.assertNotIn('ReadAllBytes',tool)
        self.assertIn('READONLY_TOKEN',tool)
        self.assertIn("$accessMode = 'readonly'",tool)
        self.assertIn("$value -eq '..'",tool)
        self.assertIn('EscapeDataString',tool)
        self.assertEqual(tool.count('$response = Send-OpenCloudRequestFallback'),1)
        self.assertIn('Protect-OpenCloudResponse',tool)
        self.assertIn('$handler.AllowAutoRedirect = $false',SOURCE)
        self.assertIn('$request.AllowAutoRedirect = $false',SOURCE)
        self.assertIn("name = 'open_cloud'",SOURCE)
        self.assertIn("'open_cloud'         { return (Invoke-OpenCloudServerTool",SOURCE)

    def test_ui_and_version(self):
        self.assertEqual(json.loads((ROOT/'version.json').read_text())['version'],'7.6.3')
        ui=function('Get-CloudPermissionCatalog','New-CloudPermissionRow')
        self.assertIn('(Get-OpenCloudCatalog).permissions.PSObject.Properties',ui)
        self.assertIn('Test-OpenCloudPermission -Info $Verdict -Permission ([string]$Item.id)',SOURCE)
        self.assertIn('gespeicherter Key bleibt unverändert',SOURCE)
        self.assertIn('Set-OpenCloudIntrospectCache $script:Shared $Verdict',SOURCE)
        self.assertTrue((ROOT/'ArenaBridge.ps1').read_bytes().startswith(b'\xef\xbb\xbf'))

if __name__=='__main__':unittest.main(verbosity=2)

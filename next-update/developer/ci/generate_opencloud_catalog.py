#!/usr/bin/env python3
"""Build the reviewed API-key allowlist; never fetch or update at runtime.
Usage: python developer/ci/generate_opencloud_catalog.py /path/to/official/openapi.json
Source revision is pinned in opencloud/catalog.json. Review upstream changes!
"""
import hashlib
import json
from pathlib import Path
import re
import sys
ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = ROOT / 'app'
REVISION = 'af5f853c78b58c4ea86d62ac2345f881ac11fcec'

def build(source):
    permissions = json.loads((APP_ROOT / 'opencloud/permissions.json').read_text())
    spec = json.loads(source)
    def resolve_non_schema_refs(value):
        if isinstance(value, list): return [resolve_non_schema_refs(v) for v in value]
        if not isinstance(value, dict): return value
        ref = value.get('$ref', '')
        if ref and not ref.startswith('#/components/schemas/'):
            assert ref.startswith('#/components/'), ref
            resolved = spec
            for segment in ref[2:].split('/'):
                resolved = resolved[segment.replace('~1', '/').replace('~0', '~')]
            return resolve_non_schema_refs(resolved)
        return {k: resolve_non_schema_refs(v) for k, v in value.items()}
    operations = []
    public = {'Cloud_GetUniverse': 'universe:read', 'Cloud_GetPlace': 'universe.place:read'}
    for path, methods in spec['paths'].items():
        for method, op in methods.items():
            if method not in ('get', 'post', 'patch', 'put', 'delete'): continue
            if not any('roblox-api-key' in s for s in op.get('security', [])): continue
            scopes = sorted({s['name'] for s in op.get('x-roblox-scopes', [])})
            # Subscription is banned even though universe:write is an alternative.
            if 'subscription' in path: continue
            # Badge update permits the non-spending write scope as an alternative.
            if path == '/legacy-badges/v1/badges/{badgeId}' and method == 'patch':
                scopes = ['legacy-universe.badge:write']
            policy_scopes = scopes or ([public[op['operationId']]] if op.get('operationId') in public else [])
            if not policy_scopes or not set(policy_scopes) <= permissions.keys(): continue
            ident = op.get('operationId') or re.sub('[^a-zA-Z0-9_]+', '_', method + '_' + path).strip('_')
            params = resolve_non_schema_refs(methods.get('parameters', []) + op.get('parameters', []))
            # Some asset operations omit path parameter declarations upstream.
            for name in re.findall(r'\{([^}]+)\}', path):
                if not any(p.get('name') == name and p.get('in') == 'path' for p in params):
                    params = params + [dict(name=name, **{'in': 'path'}, required=True, schema={'type': 'string'})]
            request = resolve_non_schema_refs(op.get('requestBody', {}))
            if ident == 'Places_CreatePlaceVersionApiKey':
                request = {'required': True, 'content': {t: {'schema': {'type': 'string', 'format': 'binary'}} for t in ['application/xml', 'application/octet-stream']}}
            # Include only transitively used definitions, not forbidden APIs.
            definitions = {}
            def refs(value):
                if isinstance(value, dict):
                    ref = value.get('$ref', '')
                    if ref.startswith('#/components/schemas/'):
                        name = ref.rsplit('/', 1)[1]
                        if name not in definitions:
                            definitions[name] = spec['components']['schemas'][name]
                            refs(definitions[name])
                    for v in value.values(): refs(v)
                elif isinstance(value, list):
                    for v in value: refs(v)
            refs(params); refs(request)
            operations.append(dict(id=ident, method=method.upper(), path=path,
                scopes=scopes, policyScopes=policy_scopes,
                readOnly=method=='get' or all(s.rsplit(':',1)[-1] in ('read','list') for s in policy_scopes),
                summary=op.get('summary') or op.get('x-roblox-cloud-api-operation-name') or ident,
                description=op.get('description',''), parameters=params, requestBody=request,
                components={'schemas': definitions}, documentation=op.get('externalDocs',{}).get('url',''),
                stability=op.get('x-roblox-stability',''), sizeLimit=op.get('x-roblox-size-limit',20971520)))
    assert len({o['id'] for o in operations}) == len(operations)
    return dict(source=f'https://github.com/Roblox/creator-docs/blob/{REVISION}/content/en-us/reference/cloud/openapi.json',
                sourceSha256=hashlib.sha256(source).hexdigest(), permissions=permissions, operations=operations)

if __name__ == '__main__':
    catalog = build(Path(sys.argv[1]).read_bytes())
    text = json.dumps(catalog,ensure_ascii=False,separators=(',',':'))
    (APP_ROOT/'opencloud/catalog.json').write_text(text+'\n')
    path = APP_ROOT/'ArenaBridge.ps1'
    ps = path.read_text(encoding='utf-8-sig')
    begin, end = '# BEGIN GENERATED OPEN CLOUD CATALOG', '# END GENERATED OPEN CLOUD CATALOG'
    block = begin+"\n    function Get-OpenCloudCatalog {\n        if ($null -eq $script:OpenCloudCatalogData) {\n            $script:OpenCloudCatalogData = @'\n"+text+"\n'@ | ConvertFrom-Json\n        }\n        return $script:OpenCloudCatalogData\n    }\n    "+end
    if begin in ps:
        ps = ps[:ps.index(begin)] + block + ps[ps.index(end)+len(end):]
    else:
        ps = ps.replace('$script:BridgeOpenCloudTools = {', '$script:BridgeOpenCloudTools = {\n    '+block, 1)
    path.write_text(ps,encoding='utf-8-sig')
    print(f'{len(catalog["permissions"])} permissions; {len(catalog["operations"])} operations')

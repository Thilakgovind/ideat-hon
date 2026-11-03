"""Prepare import files using the running ngrok tunnel; never copies API keys."""
import json
import httpx
from . import config
from .set_env import set_value


def main():
    try:
        response = httpx.get('http://127.0.0.1:4040/api/tunnels', timeout=5)
        response.raise_for_status()
        tunnels = response.json().get('tunnels', [])
        targets = [t for t in tunnels if t.get('public_url', '').startswith('https://')
                   and str(t.get('config', {}).get('addr', '')).rstrip('/').endswith(':8000')]
        if not targets:
            print('PUBLIC_BACKEND_URL: MISSING (start ngrok http 8000)')
            return 1
        url = targets[0]['public_url'].rstrip('/')
        check = httpx.get(url + '/api/veeramangai/catalog',
                         headers={'ngrok-skip-browser-warning': 'true'}, timeout=30)
        check.raise_for_status()
        catalog = check.json()
        live = catalog.get('storage', {})
        if len(live) != 5 or any(mode != 'supabase' for mode in live.values()):
            print('SUPABASE_CATALOG: FAILED')
            return 1
        for filename in ('veeramangai_supabase_catalog.json', 'veeramangai_avvai.json'):
            path = config.ROOT / 'n8n' / filename
            workflow = json.loads(path.read_text(encoding='utf-8'))
            for node in workflow['nodes']:
                params = node.get('parameters', {})
                if node['type'] == 'n8n-nodes-base.httpRequest':
                    endpoint = '/api/veeramangai/catalog' if 'catalog' in filename else '/api/veeramangai/chat'
                    params['url'] = url + endpoint
            workflow['active'] = False
            path.write_text(json.dumps(workflow, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        set_value('PUBLIC_BACKEND_URL', url)
        print('PUBLIC_BACKEND_URL: OK')
        print('SUPABASE_CATALOG: OK')
        print('N8N_IMPORT_FILES: OK')
        return 0
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        print('N8N_PREPARATION: FAILED')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

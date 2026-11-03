"""Read-only n8n management check. Outputs names/status only, never credentials."""
from urllib.parse import urlparse
import httpx
from . import config

def main():
    base=config.env('N8N_BASE_URL').rstrip('/')
    key=config.env('N8N_API_KEY')
    if not base or not key:
        print('N8N_BASE_URL: '+('OK' if base else 'MISSING'))
        print('N8N_API_KEY: '+('OK' if key else 'MISSING'))
        return 1
    parsed=urlparse(base)
    if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        print('N8N_BASE_URL: FAILED')
        return 1
    api = base if base.endswith('/api/v1') else base+'/api/v1'
    try:
        # No redirects: don't forward management credentials to another origin.
        r=httpx.get(api+'/workflows',headers={'X-N8N-API-KEY':key},params={'limit':100},timeout=10,follow_redirects=False)
        valid=r.status_code==200 and isinstance(r.json().get('data'),list)
        print('N8N_API_KEY: '+('OK' if valid else 'FAILED'))
        print('N8N_WORKFLOWS: '+('OK' if valid else 'FAILED'))
        return 0 if valid else 1
    except (httpx.HTTPError,ValueError,AttributeError):
        print('N8N_API_KEY: FAILED')
        return 1

if __name__=='__main__':
    raise SystemExit(main())

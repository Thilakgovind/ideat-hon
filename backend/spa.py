"""Static frontend serving with an explicit SPA route allowlist."""
from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles

SPA_ROOTS = {
    '', 'veeramangai', 'login', 'home', 'aval', 'booking', 'payment', 'ticket',
    'tickets', 'bus', 'metro', 'train', 'nearby', 'circle', 'trip', 'sos',
    'explore', 'place', 'reach', 'steps', 'demo', 'avvai-studio',
}


class FrontendFiles(StaticFiles):
    async def get_response(self, path, scope):
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            segments = path.replace('\\', '/').strip('/').split('/')
            # Missing API/static files must never turn into successful HTML.
            if (exc.status_code != 404 or scope['method'] not in ('GET', 'HEAD')
                    or segments[0] not in SPA_ROOTS or any('.' in s for s in segments)):
                raise
            response = await super().get_response('index.html', scope)
            response.headers['Cache-Control'] = 'no-cache'
            return response


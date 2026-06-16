"""
Zapier MCP posting connector.

Lets the app publish real social posts by calling Fred's Zapier MCP endpoint
(an authenticated HTTP/JSON-RPC server) instead of requiring per-platform OAuth
developer apps. The Zapier side already has app actions enabled (e.g. Facebook
Pages -> Create Page Post); this module invokes them via `execute_zapier_write_action`.

Config (set on Railway + locally): ZAPIER_MCP_URL, ZAPIER_MCP_TOKEN.
If unset, is_configured() is False and callers should fall back (simulate).

Design notes:
- This is the *runtime* posting path used by the deployed app's autopilot. A
  SocialAccount is marked to use it by setting webhook_url to the sentinel
  'zapier-mcp' (see services/social_media_integration.py routing). The target
  page/handle is read from the account (platform_user_id or username).
- The MCP transport is streamable HTTP: a response may be plain JSON or an SSE
  body with `data: {...}` lines; _parse handles both.
"""
import os
import json
import logging
import requests

logger = logging.getLogger(__name__)

# Map our platform names -> (Zapier selected_api, action key) for the
# "create a post" write action. Extend as more platforms are enabled in Zapier.
_PLATFORM_ACTIONS = {
    'facebook': ('FacebookV2CLIAPI', 'page_stream'),  # Facebook Pages -> Create Page Post
}


def _url():
    return os.environ.get('ZAPIER_MCP_URL', '').strip()


def _token():
    return os.environ.get('ZAPIER_MCP_TOKEN', '').strip()


def is_configured():
    return bool(_url() and _token())


def _parse(raw):
    if not raw:
        return None
    if raw.lstrip().startswith('{'):
        try:
            return json.loads(raw)
        except Exception:
            return None
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith('data:'):
            chunk = line[5:].strip()
            if chunk and chunk != '[DONE]':
                try:
                    return json.loads(chunk)
                except Exception:
                    pass
    return None


def _rpc(method, params=None):
    body = {'jsonrpc': '2.0', 'id': 1, 'method': method}
    if params is not None:
        body['params'] = params
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream',
        'Authorization': 'Bearer ' + _token(),
    }
    resp = requests.post(_url(), json=body, headers=headers, timeout=45)
    return resp.status_code, _parse(resp.text)


def _call_tool(name, arguments):
    """Run the MCP handshake then call a tool; returns (ok, parsed, error)."""
    if not is_configured():
        return False, None, 'Zapier MCP not configured (ZAPIER_MCP_URL/ZAPIER_MCP_TOKEN)'
    try:
        _rpc('initialize', {
            'protocolVersion': '2025-03-26',
            'capabilities': {},
            'clientInfo': {'name': 'dominate-marketing', 'version': '1.0'},
        })
        status, parsed = _rpc('tools/call', {'name': name, 'arguments': arguments})
        if parsed and parsed.get('error'):
            return False, parsed, parsed['error'].get('message', 'MCP error')
        if status and status >= 400:
            return False, parsed, f'MCP HTTP {status}'
        # A tool result with isError True is a soft failure.
        result = (parsed or {}).get('result', {})
        if isinstance(result, dict) and result.get('isError'):
            txt = _result_text(parsed)
            return False, parsed, txt or 'Zapier action returned an error'
        return True, parsed, None
    except Exception as e:
        return False, None, f'Zapier MCP request failed: {e}'


def _result_text(parsed):
    """Pull the text payload out of an MCP tool result, if any."""
    try:
        content = parsed['result']['content']
        return ' '.join(c.get('text', '') for c in content if isinstance(c, dict))[:1000]
    except Exception:
        return ''


def execute_write_action(selected_api, action, instructions, params, output='post id, url, and status'):
    return _call_tool('execute_zapier_write_action', {
        'selected_api': selected_api,
        'action': action,
        'instructions': instructions,
        'params': params,
        'output': output,
    })


def create_facebook_page_post(page, message, image_url=None, link_url=None):
    """Publish a Facebook Page post via Zapier. `page` is the connected Page
    (name or id) Zapier should target. Returns a dict the caller can act on."""
    selected_api, action = _PLATFORM_ACTIONS['facebook']
    params = {'message': message}
    if page:
        params['page'] = page
    if image_url:
        params['source'] = [image_url]
    if link_url:
        params['link_url'] = link_url
    instr = (
        f"Create a Facebook Page post on the page '{page or '(the connected page)'}' "
        f"with exactly this message. Attach the photo if a URL is provided."
    )
    ok, parsed, err = execute_write_action(selected_api, action, instr, params)
    return {
        'success': bool(ok),
        'error': err,
        'detail': _result_text(parsed) if parsed else '',
    }


def post(platform, target, message, image_url=None, link_url=None):
    """Generic entry point used by the posting service. Returns {success, error, detail}."""
    platform = (platform or '').lower()
    if platform == 'facebook':
        return create_facebook_page_post(target, message, image_url=image_url, link_url=link_url)
    return {'success': False, 'error': f'Zapier MCP posting not wired for "{platform}" yet', 'detail': ''}

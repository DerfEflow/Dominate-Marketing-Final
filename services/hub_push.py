"""Push Dominate clients (Brand rows) into TruAgent, Truline's AI admin hub.

TruAgent exposes a lead door at POST {TRUAGENT_URL}/leads/webhook. Whenever a
client is created or edited in Dominate (and once via `flask hub-backfill`),
we POST the client's contact card there so the hub sees every lead.

Design rules (keep these):
- Config comes ONLY from env vars TRUAGENT_URL + LEADS_SECRET. When either is
  missing the feature is DORMANT: log once, skip silently after that. This is
  how every other paid/external integration in services/ behaves.
- A hub outage must NEVER break Dominate's UX: every failure path is caught,
  logged (without secrets), and swallowed. Callers never see an exception.
- Idempotency: the hub dedupes by (client_name + address) when address is
  non-empty. Brand has no address column today, so we also always send
  data.dominate_brand_id as the stable cross-system key.
"""
import logging
import os

import requests

logger = logging.getLogger(__name__)

# Log the "not configured" situation only once per process so the worker's
# scheduler loop doesn't spam the logs every tick.
_warned_unconfigured = False


def _hub_config():
    """Return (url, secret) from the environment, or (None, None) if dormant."""
    url = (os.environ.get('TRUAGENT_URL') or '').strip().rstrip('/')
    secret = (os.environ.get('LEADS_SECRET') or '').strip()
    if not url or not secret:
        return None, None
    return url, secret


def hub_configured():
    """True when both TRUAGENT_URL and LEADS_SECRET are set."""
    url, secret = _hub_config()
    return bool(url and secret)


def build_payload(brand, event='created', secret=''):
    """Map a Brand (client) row onto TruAgent's /leads/webhook contract.

    Works on any Brand-like object (tests use a stand-in), so every attribute
    read is defensive. `monthly_retainer` is a Decimal column → float for JSON;
    `subscription_tier` is an Enum → its .value.
    """
    retainer = getattr(brand, 'monthly_retainer', None)
    if retainer is not None:
        try:
            retainer = float(retainer)
        except (TypeError, ValueError):
            retainer = None

    tier = getattr(brand, 'subscription_tier', None)
    tier = getattr(tier, 'value', tier)  # Enum -> str; plain str passes through

    # rep = the salesperson who owns this client (User backref on Brand).
    rep = None
    owner = getattr(brand, 'user', None)
    if owner is not None:
        rep = getattr(owner, 'username', None) or getattr(owner, 'email', None)

    return {
        'secret': secret,
        'source': 'dominate',
        'client_name': getattr(brand, 'name', None),
        # Brand has no address column. Send "" (NOT null): the hub's dedupe
        # loop does opp.get("address", "").lower() over STORED records, so a
        # stored null poisons the door (None.lower() → 500) for every later
        # lead from any source. "" is falsy → same no-dedupe semantics as null,
        # but safe. Verified against TruAgent main.py leads_webhook 2026-06-11.
        'address': '',
        'phone': getattr(brand, 'contact_phone', None) or None,
        'email': getattr(brand, 'contact_email', None) or None,
        'notes': getattr(brand, 'notes', None) or None,
        'rep': rep,
        'data': {
            'dominate_brand_id': getattr(brand, 'id', None),
            'status': getattr(brand, 'status', None),
            'monthly_retainer': retainer,
            'subscription_tier': tier,
            'contact_name': getattr(brand, 'contact_name', None),
            'event': event,
        },
    }


def push_lead_to_hub(brand, event='created'):
    """POST one client to TruAgent's lead door. Never raises.

    Returns (status, detail):
      ('ok', opportunity_id)  – hub accepted it
      ('skipped', reason)     – feature dormant (env vars unset)
      ('failed', reason)      – network/HTTP error, already logged
    """
    global _warned_unconfigured
    try:
        url, secret = _hub_config()
        if not url:
            if not _warned_unconfigured:
                logger.info(
                    'hub_push: TRUAGENT_URL/LEADS_SECRET not set — hub push '
                    'is dormant (this is logged once).'
                )
                _warned_unconfigured = True
            return ('skipped', 'not configured')

        payload = build_payload(brand, event=event, secret=secret)
        resp = requests.post(f'{url}/leads/webhook', json=payload, timeout=10)
        if resp.status_code >= 400:
            logger.warning(
                'hub_push: hub rejected "%s" (HTTP %s) — continuing, Dominate '
                'is unaffected.', payload.get('client_name'), resp.status_code
            )
            return ('failed', f'HTTP {resp.status_code}')

        try:
            body = resp.json()
        except ValueError:
            body = {}
        opportunity_id = body.get('opportunity_id')
        logger.info(
            'hub_push: pushed client "%s" (event=%s) → opportunity_id=%s',
            payload.get('client_name'), event, opportunity_id
        )
        return ('ok', opportunity_id)
    except Exception as e:  # noqa: BLE001 — a hub outage must never break the app
        logger.warning('hub_push: push failed (non-fatal): %s', e)
        return ('failed', str(e))

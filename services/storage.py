"""
Durable public media hosting via Supabase Storage.

Generated post images/videos must live at a public URL so social platforms
(via Zapier) can fetch them, and must survive redeploys (Railway's local
static/ is ephemeral). This uploads bytes to a public Supabase Storage bucket
and returns the permanent public URL.

Config (set on Railway web+worker + local .env):
  SUPABASE_URL          e.g. https://<ref>.supabase.co
  SUPABASE_SERVICE_KEY  the project's secret key (service_role / sb_secret_...)
  SUPABASE_BUCKET       optional, defaults to 'post-media'

If unset, is_configured() is False and callers fall back to local static/.
"""
import os
import uuid
import logging
import requests

logger = logging.getLogger(__name__)


def _url():
    return os.environ.get('SUPABASE_URL', '').strip().rstrip('/')


def _key():
    return os.environ.get('SUPABASE_SERVICE_KEY', '').strip()


def bucket():
    return os.environ.get('SUPABASE_BUCKET', 'post-media')


def is_configured():
    return bool(_url() and _key())


def upload_bytes(data, ext='png', content_type='image/png', prefix='img'):
    """Upload bytes to the public bucket; return the public URL or None."""
    if not is_configured() or not data:
        return None
    path = f"{prefix}/{uuid.uuid4().hex}.{ext}"
    try:
        r = requests.post(
            f"{_url()}/storage/v1/object/{bucket()}/{path}",
            headers={
                'Authorization': 'Bearer ' + _key(),
                'apikey': _key(),
                'Content-Type': content_type,
                'x-upsert': 'true',
            },
            data=data, timeout=45,
        )
        if r.status_code in (200, 201):
            return f"{_url()}/storage/v1/object/public/{bucket()}/{path}"
        logger.warning(f"Supabase Storage upload failed {r.status_code}: {r.text[:200]}")
    except Exception as e:
        logger.warning(f"Supabase Storage upload error: {e}")
    return None

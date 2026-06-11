"""Tests for services/hub_push.py (TruAgent hub integration).

Plain unittest (pytest is not in the venv). Run from the app root:
    ./venv/Scripts/python.exe -m unittest tests.test_hub_push -v

No network, no database: the Brand is a stand-in object and requests.post is
mocked. The three guarantees under test:
  1. A Brand row maps onto TruAgent's /leads/webhook contract correctly.
  2. The feature is dormant (skip, no POST) when env vars are unset.
  3. A hub outage is swallowed — push_lead_to_hub never raises.
"""
import os
import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest import mock

import requests

from services.hub_push import build_payload, hub_configured, push_lead_to_hub


def fake_brand(**overrides):
    """A Brand-like object with the fields hub_push reads."""
    fields = dict(
        id='brand-uuid-123',
        name='Summit Roofing Co',
        contact_name='Sam Summit',
        contact_email='sam@summitroofing.test',
        contact_phone='555-0100',
        notes='Long-time roofing client.',
        status='active',
        monthly_retainer=Decimal('1500.00'),
        subscription_tier=SimpleNamespace(value='pro'),  # Enum stand-in
        user=SimpleNamespace(username='fredwolfe2000',
                             email='fredwolfe@gmail.com'),
    )
    fields.update(overrides)
    return SimpleNamespace(**fields)


CONFIGURED_ENV = {'TRUAGENT_URL': 'https://hub.test', 'LEADS_SECRET': 'unit-test-secret'}
UNCONFIGURED_ENV = {'TRUAGENT_URL': '', 'LEADS_SECRET': ''}


class TestBuildPayload(unittest.TestCase):
    def test_maps_brand_fields_to_contract(self):
        payload = build_payload(fake_brand(), event='created', secret='unit-test-secret')

        self.assertEqual(payload['secret'], 'unit-test-secret')
        self.assertEqual(payload['source'], 'dominate')
        self.assertEqual(payload['client_name'], 'Summit Roofing Co')
        # Brand has no address column. Must be "" (never null): the hub's
        # dedupe loop crashes on stored null addresses (None.lower() → 500).
        self.assertEqual(payload['address'], '')
        self.assertEqual(payload['phone'], '555-0100')
        self.assertEqual(payload['email'], 'sam@summitroofing.test')
        self.assertEqual(payload['notes'], 'Long-time roofing client.')
        self.assertEqual(payload['rep'], 'fredwolfe2000')

        data = payload['data']
        self.assertEqual(data['dominate_brand_id'], 'brand-uuid-123')
        self.assertEqual(data['status'], 'active')
        self.assertEqual(data['monthly_retainer'], 1500.0)  # Decimal -> float
        self.assertEqual(data['subscription_tier'], 'pro')  # Enum -> value
        self.assertEqual(data['contact_name'], 'Sam Summit')
        self.assertEqual(data['event'], 'created')

    def test_handles_sparse_brand(self):
        brand = fake_brand(contact_email=None, contact_phone=None, notes=None,
                           monthly_retainer=None, subscription_tier=None,
                           user=None)
        payload = build_payload(brand, event='updated', secret='s')
        self.assertIsNone(payload['phone'])
        self.assertIsNone(payload['email'])
        self.assertIsNone(payload['notes'])
        self.assertIsNone(payload['rep'])
        self.assertIsNone(payload['data']['monthly_retainer'])
        self.assertIsNone(payload['data']['subscription_tier'])
        self.assertEqual(payload['data']['event'], 'updated')

    def test_rep_falls_back_to_owner_email(self):
        brand = fake_brand(user=SimpleNamespace(username=None,
                                                email='rep@dominate.test'))
        payload = build_payload(brand, secret='s')
        self.assertEqual(payload['rep'], 'rep@dominate.test')


class TestPushLeadToHub(unittest.TestCase):
    @mock.patch.dict(os.environ, UNCONFIGURED_ENV)
    @mock.patch('services.hub_push.requests.post')
    def test_dormant_when_unconfigured(self, mock_post):
        self.assertFalse(hub_configured())
        status, detail = push_lead_to_hub(fake_brand(), event='created')
        self.assertEqual(status, 'skipped')
        mock_post.assert_not_called()

    @mock.patch.dict(os.environ, CONFIGURED_ENV)
    @mock.patch('services.hub_push.requests.post')
    def test_posts_payload_and_returns_opportunity_id(self, mock_post):
        mock_post.return_value = mock.Mock(
            status_code=200,
            json=lambda: {'status': 'ok', 'opportunity_id': 42},
        )
        status, detail = push_lead_to_hub(fake_brand(), event='created')

        self.assertEqual((status, detail), ('ok', 42))
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], 'https://hub.test/leads/webhook')
        self.assertEqual(kwargs['timeout'], 10)
        body = kwargs['json']
        self.assertEqual(body['secret'], 'unit-test-secret')
        self.assertEqual(body['client_name'], 'Summit Roofing Co')
        self.assertEqual(body['data']['dominate_brand_id'], 'brand-uuid-123')

    @mock.patch.dict(os.environ, CONFIGURED_ENV)
    @mock.patch('services.hub_push.requests.post')
    def test_connection_error_is_swallowed(self, mock_post):
        mock_post.side_effect = requests.exceptions.ConnectionError('hub down')
        try:
            status, detail = push_lead_to_hub(fake_brand(), event='updated')
        except Exception as e:  # pragma: no cover
            self.fail(f'push_lead_to_hub raised {e!r}; it must never raise')
        self.assertEqual(status, 'failed')
        self.assertIn('hub down', detail)

    @mock.patch.dict(os.environ, CONFIGURED_ENV)
    @mock.patch('services.hub_push.requests.post')
    def test_http_error_is_swallowed(self, mock_post):
        mock_post.return_value = mock.Mock(status_code=500, json=lambda: {})
        status, detail = push_lead_to_hub(fake_brand())
        self.assertEqual((status, detail), ('failed', 'HTTP 500'))


if __name__ == '__main__':
    unittest.main()

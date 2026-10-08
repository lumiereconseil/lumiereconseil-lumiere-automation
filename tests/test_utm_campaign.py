"""Regression tests for campaign attribution URL construction."""

import unittest
from urllib.parse import parse_qs, urlsplit
from libs.utm_campaign import build_campaign_url


class CampaignURLTests(unittest.TestCase):
    def test_attribution_and_existing_parameters(self):
        url = build_campaign_url(
            "https://lumiereconseilai21.wordpress.com/?ref=existing&utm_source=old#diagnosis",
            source="bluesky", campaign="tokutabi_20261008", content="morning_0930")
        parsed = urlsplit(url)
        query = parse_qs(parsed.query)
        self.assertEqual(query["ref"], ["existing"])
        self.assertEqual(query["utm_source"], ["bluesky"])
        self.assertEqual(query["utm_medium"], ["organic_social"])
        self.assertEqual(query["utm_campaign"], ["tokutabi_20261008"])
        self.assertEqual(query["utm_content"], ["morning_0930"])
        self.assertEqual(parsed.fragment, "diagnosis")

    def test_reject_insecure_urls_and_invalid_campaign(self):
        for base in ("http://example.com", "https://user:pass@example.com", "file:///etc/passwd"):
            with self.assertRaises(ValueError):
                build_campaign_url(base, source="instagram", campaign="tokutabi_20261008", content="a1")
        with self.assertRaises(ValueError):
            build_campaign_url("https://example.com", source="unknown", campaign="tokutabi_20261008", content="a1")
        with self.assertRaises(ValueError):
            build_campaign_url("https://example.com", source="instagram", campaign="bad campaign", content="a1")


if __name__ == "__main__":
    unittest.main()

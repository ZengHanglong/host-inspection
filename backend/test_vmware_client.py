import unittest
from datetime import datetime, timedelta, timezone

from app.services.vmware_client import VMwareClient


class VMwareClientDateTests(unittest.TestCase):
    def test_days_since_handles_timezone_aware_datetime(self):
        client = VMwareClient(host="", username="", password="")
        value = datetime.now(timezone.utc) - timedelta(days=5)

        days = client._days_since(value)

        self.assertGreaterEqual(days, 5)

    def test_days_since_handles_naive_datetime(self):
        client = VMwareClient(host="", username="", password="")
        value = datetime.now() - timedelta(days=3)

        days = client._days_since(value)

        self.assertGreaterEqual(days, 3)


if __name__ == '__main__':
    unittest.main()

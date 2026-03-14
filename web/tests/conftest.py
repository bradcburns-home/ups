import sys
from unittest.mock import MagicMock

google_mock = MagicMock()
sys.modules.setdefault("google", google_mock)
sys.modules.setdefault("google.cloud", google_mock.cloud)
sys.modules.setdefault("google.cloud.bigquery", google_mock.cloud.bigquery)

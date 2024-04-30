"""
Test the custom management commands.
"""
from unittest.mock import patch, MagicMock

from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import SimpleTestCase


class CommandTests(SimpleTestCase):
    """
    Test the custom management commands.
    """

    @patch('django.db.utils.ConnectionHandler.__getitem__')
    def test_wait_for_db_ready(self, mock_getitem):
        """
        Test waiting for db when db is available.
        """
        # Simulate OperationalError on the first call, then return a connection object
        mock_getitem.side_effect = [OperationalError("Database unavailable"), MagicMock()]

        call_command('wait_for_db')

        # Check if __getitem__ was called more than once
        self.assertTrue(mock_getitem.call_count > 1)
    
    @patch('time.sleep')
    def test_wait_for_db_delay(self, mock_sleep):
        """
        Test waiting for db with retries.
        """
        with patch('django.db.utils.ConnectionHandler.__getitem__') as gi:
            # Simulate OperationalError for the first 5 calls, then return a mock connection
            gi.side_effect = [OperationalError("Database unavailable")]*5 + [MagicMock()]

            call_command('wait_for_db')

            # Assert that getitem was called 6 times: 5 failures + 1 success
            self.assertEqual(gi.call_count, 6)
            # Optionally, assert that sleep was called 5 times (one for each retry)
            self.assertEqual(mock_sleep.call_count, 5)

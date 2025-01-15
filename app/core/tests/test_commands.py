"""
Test custom Django management commands.
"""
from unittest.mock import patch
from psycopg2 import OperationalError as Psycopg2Error
from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import SimpleTestCase


@patch('core.management.commands.wait_for_db.Command.check')
class CommandTests(SimpleTestCase):
    """Tests for the wait_for_db management command."""

    def test_wait_for_db_ready(self, patched_check):
        """Test the command when the database is ready."""
        patched_check.return_value = True

        call_command('wait_for_db')

        patched_check.assert_called_once_with(databases=['default'])

    @patch('time.sleep')
    def test_wait_for_db_delay(self, patched_sleep, patched_check):
        """
        Test the command when the database raises connection errors initially.
        """
        side_effect_sequence = [Psycopg2Error] * 2 + [OperationalError] * 3 + [True]
        patched_check.side_effect = side_effect_sequence

        call_command('wait_for_db')

        self.assertEqual(patched_check.call_count, 6)
        patched_check.assert_called_with(databases=['default'])

    def test_wait_for_db_with_custom_timeout(self, patched_check):
        """Test the command with custom timeout."""
        patched_check.return_value = True

        call_command('wait_for_db', timeout=10)

        patched_check.assert_called_once_with(databases=['default'])

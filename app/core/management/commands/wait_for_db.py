"""
Django command to wait for the database to be available.
"""
import time
import logging
from psycopg2 import OperationalError as Psycopg2OpError
from django.core.management.base import BaseCommand
from django.db.utils import OperationalError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Django wait for database command."""

    def add_arguments(self, parser):
        """Add custom arguments to the command."""
        parser.add_argument(
            '--wait-time',
            type=int,
            default=1,
            help='Time to wait between database connection retries in seconds.',
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=60,
            help='Maximum time to wait for the database to be available in seconds.',
        )

    def handle(self, *args, **options):
        """Entry point for the wait_for_db command."""
        wait_time = options['wait_time']
        timeout = options['timeout']

        logger.info('Waiting for database...')
        database_ready = False
        start_time = time.time()

        while not database_ready:
            if time.time() - start_time > timeout:
                self.stderr.write(self.style.ERROR('Timeout: Database unavailable.'))
                raise Exception('Database is still unavailable after waiting.')

            try:
                self.check(databases=['default'])
                database_ready = True
            except (Psycopg2OpError, OperationalError):
                logger.warning(f'Database unavailable, waiting for {wait_time} seconds...')
                time.sleep(wait_time)

        self.stdout.write(self.style.SUCCESS('Database available!'))

"""
Self-contained daily scheduler for the trash purge.

This runs the purge automatically once every 24 hours without requiring cron,
systemd, Celery, or any external service. It is started from core/apps.py and
runs in a daemon background thread inside the Django process itself, so it
works identically in development (runserver) and in production (gunicorn, etc.).

Design notes:
- Zero performance impact: the thread sleeps ~24h between runs and each run is
  a few quick DELETE queries. It never touches request handling.
- Zero security impact: no new URLs, views, or auth surface are exposed.
- Deployment-independent: no cron/systemd/OS dependency; it just needs the
  Django process to be alive (which it always is when the site is running).
- A file lock ensures only ONE process (out of multiple gunicorn workers)
  actually starts the scheduler thread, avoiding redundant timers.
- The purge itself is idempotent, so even if two threads ever ran it, no data
  would be double-deleted.
"""
import os
import threading
import time
import fcntl

from django.utils import timezone
from datetime import timedelta

from .management.commands.purge_trash import purge_trash

# How often to run the purge (seconds). 24 hours.
INTERVAL_SECONDS = 24 * 60 * 60

# Lock file used to guarantee a single scheduler across processes.
_LOCK_PATH = os.path.join('/tmp', 'boycott_pk_purge_scheduler.lock')

# In-process guard: ensures only ONE scheduler thread per Python process
# (the file lock alone does not cover multiple threads in the same process,
# because flock locks are per open-file-description, not per thread).
_started = False
_started_lock = threading.Lock()


def _scheduler_loop():
    """Background loop: run purge, then sleep until the next interval."""
    # Run once shortly after startup so the first run doesn't wait a full day.
    time.sleep(60)
    while True:
        try:
            purge_trash()
        except Exception:
            # Never let a failure kill the scheduler thread.
            pass
        time.sleep(INTERVAL_SECONDS)


def start_scheduler():
    """Start the daily purge scheduler in a daemon thread (once per host)."""
    global _started
    with _started_lock:
        if _started:
            return
        try:
            lock_file = open(_LOCK_PATH, 'w')
            # Non-blocking exclusive lock: only the first process succeeds.
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, IOError):
            # Another process already holds the lock -> it owns the scheduler.
            return
        _started = True

    thread = threading.Thread(target=_scheduler_loop, name='trash-purge-scheduler', daemon=True)
    thread.start()

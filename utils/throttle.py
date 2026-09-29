# -*- coding: utf-8 -*-

# Attempt counting for login and account creation. Kept in Postgres rather
# than in memory because every Vercel instance is its own process: a counter
# in one would never see the attempts that landed on another.

import os
import psycopg2 as pg

from flask import make_response, request
from math import ceil


# (kind, attempts allowed, window in seconds)
LOGIN_FAILURE_USER = ('login_user', 10, 15 * 60)
LOGIN_FAILURE_IP = ('login_ip', 30, 15 * 60)
SIGNUP_IP = ('signup_ip', 5, 60 * 60)

# Rows older than every window are dead weight; each write prunes them
RETENTION = '1 day'


def client_ip():
    # Vercel sets X-Forwarded-For to the connecting client's address rather
    # than appending to one the client sent, so its first entry is the client
    forwarded = request.headers.get('X-Forwarded-For', '')

    return forwarded.split(',')[0].strip() or request.remote_addr or 'unknown'


def wait_seconds(checks):
    # checks: [(rule, subject), ...]; returns how long until every rule is
    # under its limit again, or 0 if none is at it
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    wait = 0

    for (kind, limit, window), subject in checks:
        cursor.execute(
            """
            SELECT count(*),
                   extract(epoch FROM min(attempted_at)
                           + make_interval(secs => %(window)s) - now())
              FROM auth_attempt
             WHERE kind = %(kind)s AND subject = %(subject)s
                   AND attempted_at > now() - make_interval(secs => %(window)s);
            """,
            {'kind': kind, 'subject': subject, 'window': window}
            )

        count, remaining = cursor.fetchone()

        if count >= limit:
            wait = max(wait, ceil(remaining), 1)

    cursor.close()
    conn.close()

    return wait


def too_many(wait):
    return make_response('Too many attempts. Try again later.', 429,
        {'Retry-After': str(wait)})


def record(checks):
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM auth_attempt
         WHERE attempted_at < now() - %(retention)s::interval;
        """,
        {'retention': RETENTION}
        )

    for (kind, _, _), subject in checks:
        cursor.execute(
            """
            INSERT INTO auth_attempt (kind, subject)
                 VALUES (%(kind)s, %(subject)s);
            """,
            {'kind': kind, 'subject': subject}
            )

    conn.commit()

    cursor.close()
    conn.close()


def clear(rule, subject):
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM auth_attempt
         WHERE kind = %(kind)s AND subject = %(subject)s;
        """,
        {'kind': rule[0], 'subject': subject}
        )

    conn.commit()

    cursor.close()
    conn.close()

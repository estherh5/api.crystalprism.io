#!/usr/bin/env python3
import argparse
import os
import psycopg2 as pg


def initialize_database():
    # Set up database connection with environment variable
    conn = pg.connect(os.environ['DB_CONNECTION'])

    cursor = conn.cursor()

    # Create status type, UUID extension for member_id generation, and database
    # tables
    cursor.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status') THEN
                CREATE TYPE status AS ENUM ('active', 'deleted');
            END IF;
        END
        $$;

        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

        CREATE TABLE IF NOT EXISTS cp_user (
        about varchar(110),
        background_color char(7) NOT NULL DEFAULT '#ffffff',
        created text NOT NULL DEFAULT to_char
        (now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        email text UNIQUE,
        email_public boolean DEFAULT false,
        first_name varchar(50),
        icon_color char(7) NOT NULL DEFAULT '#000000',
        is_admin boolean NOT NULL DEFAULT false,
        is_owner boolean NOT NULL DEFAULT false,
        last_name varchar(50),
        member_id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
        name_public boolean DEFAULT false,
        password text NOT NULL,
        status status NOT NULL DEFAULT 'active',
        username varchar(50) UNIQUE NOT NULL);

        CREATE UNIQUE INDEX ON cp_user (is_owner) WHERE is_owner = true;

        CREATE TABLE IF NOT EXISTS rhythm_score (
        created text NOT NULL DEFAULT to_char
        (now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        member_id uuid REFERENCES cp_user(member_id) ON DELETE CASCADE,
        score int NOT NULL,
        score_id SERIAL PRIMARY KEY);

        CREATE TABLE IF NOT EXISTS shapes_score (
        created text NOT NULL DEFAULT to_char
        (now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        member_id uuid REFERENCES cp_user(member_id) ON DELETE CASCADE,
        score int NOT NULL,
        score_id SERIAL PRIMARY KEY);

        CREATE TABLE IF NOT EXISTS post (
        content text NOT NULL,
        created text NOT NULL DEFAULT to_char
        (now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        member_id uuid REFERENCES cp_user(member_id) ON DELETE CASCADE,
        post_id SERIAL PRIMARY KEY,
        public boolean NOT NULL DEFAULT false,
        title varchar(25) NOT NULL);

        CREATE TABLE IF NOT EXISTS comment (
        comment_id SERIAL PRIMARY KEY,
        content text NOT NULL,
        created text NOT NULL DEFAULT to_char
        (now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        member_id uuid REFERENCES cp_user(member_id) ON DELETE CASCADE,
        post_id int REFERENCES post(post_id) ON DELETE CASCADE);

        CREATE TABLE IF NOT EXISTS drawing (
        created text NOT NULL DEFAULT to_char
        (now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        drawing_id SERIAL PRIMARY KEY,
        member_id uuid REFERENCES cp_user(member_id) ON DELETE CASCADE,
        title varchar(25) NOT NULL,
        url text NOT NULL,
        views int NOT NULL DEFAULT 0);

        CREATE TABLE IF NOT EXISTS drawing_like (
        created text NOT NULL DEFAULT to_char
        (now() at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
        drawing_id int REFERENCES drawing(drawing_id) ON DELETE CASCADE,
        drawing_like_id SERIAL PRIMARY KEY,
        member_id uuid REFERENCES cp_user(member_id) ON DELETE CASCADE);
        """
        )

    conn.commit()

    cursor.close()
    conn.close()

    print('Database ' + os.environ['DB_NAME'] + ' initialized successfully.')

    return


# Add argument for initializing database in CLI
parser = argparse.ArgumentParser(description='Management commands')
parser.add_argument('action', type=str, help="an action for the database")
args = parser.parse_args()
if args.action == 'init_db':
    initialize_database()

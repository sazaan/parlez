"""Email syntax/uniqueness and non-destructive upgrades of legacy accounts."""
import json
import sqlite3
from unittest.mock import patch

import bcrypt
import pytest
from sqlalchemy.exc import IntegrityError

import db
import main


def signup(client, **overrides):
    return client.post('/api/auth/signup', json={
        'username': 'newlearner', 'password': 'password123',
        'email': 'Learner@EXAMPLE.COM', **overrides,
    })


@pytest.mark.parametrize('email', ['', ' ', 'not-an-email', 'learner@', '@example.com',
                                   'learner@example', 'A Person <a@example.com>',
                                   'a b@example.com', 'a\nb@example.com', 'a@127.0.0.1'])
def test_rejects_invalid_email(client, email):
    response = signup(client, email=email)
    assert response.status_code == 400
    assert 'valid email' in response.json()['detail']
    assert not main.storage.username_exists('newlearner')


def test_email_required_for_new_signup(client):
    response = client.post('/api/auth/signup', json={'username': 'learner', 'password': 'password123'})
    assert response.status_code == 422


def test_normalized_email_persists_through_progress_updates(client):
    response = signup(client, email=' Learner+French@EXAMPLE.COM ')
    assert response.status_code == 200
    user = main.storage.get_user_by_username('newlearner')
    assert user['email'] == 'learner+french@example.com'
    user['progress']['xp'] = 10
    main.storage.save_user(user)
    assert main.storage.get_user_by_id(user['id'])['email'] == 'learner+french@example.com'


def test_case_insensitive_duplicate_email(client):
    assert signup(client).status_code == 200
    duplicate = signup(client, username='different', email=' learner@example.com ')
    assert duplicate.status_code == 409
    assert not main.storage.username_exists('different')


def test_database_enforces_uniqueness_if_precheck_races(client):
    assert signup(client).status_code == 200
    with patch.object(main.storage, 'email_exists', return_value=False):
        response = signup(client, username='different')
    assert response.status_code == 409
    assert not main.storage.username_exists('different')


@pytest.mark.parametrize('password', ['a' * 73, 'é' * 37])
def test_password_does_not_silently_truncate_at_bcrypt_limit(client, password):
    response = signup(client, password=password)
    assert response.status_code == 400
    assert '72 UTF-8 bytes' in response.json()['detail']


def test_old_database_upgrade_preserves_accounts_and_is_repeatable(tmp_path):
    path = tmp_path / 'legacy.db'
    password_hash = bcrypt.hashpw(b'legacy-password', bcrypt.gensalt()).decode()
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE users (id VARCHAR PRIMARY KEY, username VARCHAR UNIQUE NOT NULL, '
                     'password_hash TEXT NOT NULL, data JSON NOT NULL)')
        conn.execute('INSERT INTO users VALUES (?, ?, ?, ?)',
                     ('old', 'legacy', password_hash, json.dumps({'progress': {'xp': 150}})))
    for _ in range(2):
        storage = db.Storage(f'sqlite:///{path}')
        try:
            user = storage.get_user_by_id('old')
            assert user['email'] is None
            assert user['progress']['xp'] == 150
            assert storage.verify_user('legacy', 'legacy-password') == 'old'
        finally:
            storage.close()
    storage = db.Storage(f'sqlite:///{path}')
    try:
        storage.create_user('new', password_hash, email='new@example.com')
        with pytest.raises(IntegrityError):
            storage.create_user('second', password_hash, email='new@example.com')
        # Existing users may continue without an email; NULL is not a shared address.
        storage.create_user('legacy2', password_hash)
    finally:
        storage.close()


def test_legacy_account_can_still_log_in(client):
    hashed = bcrypt.hashpw(b'legacy-password', bcrypt.gensalt()).decode()
    main.storage.create_user('legacy', hashed)
    response = client.post('/api/auth/login', json={'username': 'legacy', 'password': 'legacy-password'})
    assert response.status_code == 200

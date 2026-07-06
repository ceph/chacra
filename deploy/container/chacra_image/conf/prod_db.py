# {{ ansible_managed }}

sqlalchemy = {
    'url': 'postgresql+psycopg2://postgres:example@127.0.0.1/chacra',
    'echo':          False,
    'echo_pool':     False,
    'pool_recycle':  3600,
    'encoding':      'utf-8'
}

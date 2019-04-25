from pecan import conf
import base64


def make_credentials(correct=True, username=None, secret=None):
    if correct and not username and not secret:
        creds = "%s:%s" % (conf.api_user, conf.api_key)
    elif username and secret:
        creds = "%s:%s" % (username, secret)
    else:
        creds = 'you:wrong'
    garbled_creds = base64.b64encode(creds.encode('utf-8')).decode('utf8')
    return 'Basic %s' % garbled_creds


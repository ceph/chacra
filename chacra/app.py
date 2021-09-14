from pecan import make_app
from chacra import models, asynch


def setup_app(config):

    models.init_model()
    app_conf = dict(config.app)

    app = make_app(
        app_conf.pop('root'),
        logging=getattr(config, 'logging', {}),
        **app_conf
    )

    # make a series of health checks, post if they are good
    asynch.post_if_healthy()

    return app

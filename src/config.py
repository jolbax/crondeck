import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    Testing = False


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
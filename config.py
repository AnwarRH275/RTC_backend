import os
from decouple import config

BASE_DIR = os.path.dirname(os.path.realpath(__file__))


class Config:
    SECRET_KEY = config('SECRET_KEY', default='dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = config(
        'SQLALCHEMY_TRACK_MODIFICATIONS', cast=bool, default=False)
    
    # Configuration Stripe
    STRIPE_MODE = config('STRIPE_MODE', default='test')
    STRIPE_CURRENCY = config('STRIPE_CURRENCY', default='usd')

    STRIPE_TEST_SECRET_KEY = config('STRIPE_TEST_SECRET_KEY', default='sk_test_51RPoNBGWv7C2JcFAqsnTf4QtehR3Bge5T35DKVCSqTqqpkWxAs2qiFNPgndEksL540qAwc3OffRAgYMduzeJcCUH00IK3zt5yC')
    STRIPE_LIVE_SECRET_KEY = config('STRIPE_LIVE_SECRET_KEY', default='')
    STRIPE_TEST_WEBHOOK_SECRET = config('STRIPE_TEST_WEBHOOK_SECRET', default='whsec_test_webhook_secret')
    STRIPE_LIVE_WEBHOOK_SECRET = config('STRIPE_LIVE_WEBHOOK_SECRET', default='')
    
    # IDs de produits Stripe
    STRIPE_LIVE_PRODUCT_STANDARD = config('STRIPE_LIVE_PRODUCT_STANDARD', default='')
    STRIPE_LIVE_PRODUCT_PERFORMANCE = config('STRIPE_LIVE_PRODUCT_PERFORMANCE', default='')
    STRIPE_LIVE_PRODUCT_PRO = config('STRIPE_LIVE_PRODUCT_PRO', default='')
    
    # IDs de produits Stripe TEST (valeurs par défaut)
    STRIPE_TEST_PRODUCT_STANDARD = config('STRIPE_TEST_PRODUCT_STANDARD', default='')
    STRIPE_TEST_PRODUCT_PERFORMANCE = config('STRIPE_TEST_PRODUCT_PERFORMANCE', default='')
    STRIPE_TEST_PRODUCT_PRO = config('STRIPE_TEST_PRODUCT_PRO', default='')


class DevConfig(Config):
    # Permet d'utiliser DATABASE_URL si présent, sinon on retombe sur SQLite dev.db
    #SQLALCHEMY_DATABASE_URI = config('DATABASE_URL', default="sqlite:///"+os.path.join(BASE_DIR, 'dev.db'))
    SQLALCHEMY_DATABASE_URI = "sqlite:///"+os.path.join(BASE_DIR, 'dev.db')
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProdConfig(Config):
    STRIPE_MODE = 'live'
    SQLALCHEMY_DATABASE_URI = config('DATABASE_URL', default="sqlite:///"+os.path.join(BASE_DIR, 'prod.db'))
    DEBUG = False
    SQLALCHEMY_ECHO = False


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///"+os.path.join(BASE_DIR, 'test.db')
    #DEBUG = True
    SQLALCHEMY_ECHO = False
    TESTING = True

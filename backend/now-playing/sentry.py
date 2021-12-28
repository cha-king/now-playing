import sentry_sdk


SENTRY_URL = "https://3d6894ab660f4b67bfa70234dcc4ed58@o561180.ingest.sentry.io/5697737"


def init():
    sentry_sdk.init(SENTRY_URL, traces_sample_rate=1.0)

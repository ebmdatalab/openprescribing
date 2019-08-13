from matrixstore.tests.matrixstore_factory import (
    matrixstore_from_postgres,
    patch_global_matrixstore,
)


def copy_fixtures_to_matrixstore(cls):
    """
    Decorator for TestCase classes which copies data from Postgres into an
    in-memory MatrixStore instance. This allows us to re-use database fixtures,
    and the tests designed to work with those fixtures, to test
    MatrixStore-powered code.
    """
    # These methods have been decorated with `@classmethod` so we need to use
    # `__func__` to get a reference to the original, undecorated method
    decorated_setUpClass = cls.setUpClass.__func__
    decorated_tearDownClass = cls.tearDownClass.__func__

    def setUpClass(inner_cls):
        decorated_setUpClass(inner_cls)
        matrixstore = matrixstore_from_postgres()
        stop_patching = patch_global_matrixstore(matrixstore)
        # Have to wrap this in a staticmethod decorator otherwise Python thinks
        # we're trying to create a new class method
        inner_cls._stop_patching = staticmethod(stop_patching)

    def tearDownClass(inner_cls):
        inner_cls._stop_patching()
        decorated_tearDownClass(inner_cls)

    cls.setUpClass = classmethod(setUpClass)
    cls.tearDownClass = classmethod(tearDownClass)
    return cls

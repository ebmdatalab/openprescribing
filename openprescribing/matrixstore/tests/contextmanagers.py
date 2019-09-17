from contextlib import contextmanager

from matrixstore.tests.matrixstore_factory import (
    matrixstore_from_data_factory,
    patch_global_matrixstore,
)


@contextmanager
def patched_global_matrixstore(matrixstore):
    """Context manaager that patches the global MatrixStore instance with the supplied
    matrixstore.
    """
    stop_patching = patch_global_matrixstore(matrixstore)
    try:
        yield
    finally:
        stop_patching()


@contextmanager
def patched_global_matrixstore_from_data_factory(factory):
    """Context manaager that patches the global MatrixStore instance with one built from
    the supplied factory.
    """
    matrixstore = matrixstore_from_data_factory(factory)
    with patched_global_matrixstore(matrixstore):
        yield

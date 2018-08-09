import os


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        import errno
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def find_files(path):
    paths = []
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            paths.append(os.path.join(dirpath, filename))
    return paths


def get_input():
    return input('> ')

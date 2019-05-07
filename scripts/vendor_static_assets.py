#!/usr/bin/env python
import os

import requests


FILES = {
    'datatables/datatables-bs.css': 'https://cdn.datatables.net/v/bs/dt-1.10.15/datatables.min.css',
    'datatables/datatables-bs.js': 'https://cdn.datatables.net/v/bs/dt-1.10.15/datatables.min.js',
}

BOOTSTRAP_BASE_URL = 'https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/3.3.5/'
BOOTSTRAP_FILES = [
    'fonts/glyphicons-halflings-regular.{}'.format(ext)
    for ext in ['eot', 'woff2', 'woff', 'ttf', 'svg']
]
BOOTSTRAP_FILES.append('css/bootstrap.css')

FILES.update({
    'bootstrap/' + name: BOOTSTRAP_BASE_URL + name
    for name in BOOTSTRAP_FILES
})

DIRECTORY = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        '../openprescribing/static/vendor'
    )
)


if __name__ == '__main__':
    for filename, url in FILES.items():
        path = os.path.join(DIRECTORY, filename)
        print('Downloading {}'.format(url))
        response = requests.get(url)
        response.raise_for_status()
        print('    saving to {}'.format(path))
        subdirectory = os.path.dirname(path)
        if not os.path.exists(subdirectory):
            os.makedirs(subdirectory)
        with open(path, 'wb') as f:
            f.write(response.content)

#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    if 'DJANGO_SETTINGS_MODULE' not in os.environ:
        if sys.argv[1] in ['test', 'pipeline_e2e_tests']:
            settings = 'test'
        else:
            settings = 'local'
        os.environ["DJANGO_SETTINGS_MODULE"] = (
            "openprescribing.settings.%s" % settings)

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)

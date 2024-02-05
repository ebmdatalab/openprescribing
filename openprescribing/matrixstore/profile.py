"""
Basic profiling code for working out where we're spending our time

Invoke with:
./manage.py shell -c 'from matrixstore.profile import profile; profile()'

Currently set up to profile the total spending code, but easy to adapt to
profile other functions (e.g. PPU savings - see commented out code)
"""

import datetime
import time
from cProfile import Profile

# from frontend.price_per_unit.savings import get_all_savings_for_orgs
from api.views_spending import _get_total_prescribing_entries


def test():
    # get_all_savings_for_orgs("2019-11-01", "ccg", ["99C"])
    # get_all_savings_for_orgs("2019-11-01", "all_standard_practices", [None])
    list(_get_total_prescribing_entries(["02"]))


def profile():
    num_attempts = 5
    attempts = []
    for _ in range(num_attempts):
        profiler = Profile()
        start = time.time()
        profiler.runcall(test)
        duration = time.time() - start
        attempts.append((duration, profiler))
    attempts.sort()
    profile_file = "profile.{}.prof".format(
        datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    )
    attempts[0][1].dump_stats(profile_file)
    print(
        "{}s (best of {}), profile saved as: {}".format(
            attempts[0][0], num_attempts, profile_file
        )
    )

#!/bin/bash

# We want to exit with an error if any check fails, but we want all checks to
# run each time so we get all the error messages, so we track the error status
# manually.
status=0

black --check --diff \
  --target-version py27 \
  --exclude '/migrations/' \
  .
status=$(( $status + $? ))

# We should add a pyflakes check here and probably something like jshint for
# our JavaScript as well

# We add up all the exit statuses of the lint commands. If the total is
# greater than zero then at least one command failed so we exit with an error
# status.
if [[ "$status" > 0 ]]; then
  status=1
fi

exit "$status"

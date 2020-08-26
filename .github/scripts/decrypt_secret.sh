#!/bin/sh

# Decrypt the file
gpg --quiet --batch --yes --decrypt --passphrase="$GOOGLE_CLOUD_GITHUB_ACTIONS_PASSPHRASE" \
--output google-credentials.json google-credentials-githubactions.json.gpg

There are two playbooks, `travis.yml` and `vagrant.yml`.

The former is to install the app with a Travis docker environment, so
we can run integration tests there.  It installs directly to the host
where it's running (i.e. a Travis docker container).

The latter is for a developer to get a sandbox running within a
virtualbox. It installs over ssh.

Both these playbooks set up the `environment` file by copying
`environment-sample` and doing a search-and-replace on any variables
defined as `envvars` in `ansible/vars.yml`.

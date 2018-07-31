# Turn all deprecation warnings into errors apart from those thrown in the
# allauth tag libraries, which we don't actually use but somehow end up being
# imported by Django's templete loader
export PYTHONWARNINGS=error::DeprecationWarning,\
	ignore::DeprecationWarning:allauth.account.templatetags.account_tags,\
	ignore::DeprecationWarning:allauth.socialaccount.templatetags.socialaccount_tags

test :
	cp ../environment-test ../environment
	coverage run manage.py test -v 2 --liveserver=0.0.0.0:6080-6580
	coverage report
	cd media/js; npm run test

run_smoketests :
	python smoketests/smoke.py

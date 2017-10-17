test :
	coverage run manage.py test -v 2 --liveserver=0.0.0.0:6080
	coverage report
	cd media/js; npm run test

run_smoketests :
	python smoketests/smoke.py

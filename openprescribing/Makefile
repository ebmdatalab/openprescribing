test :
	cp ../environment-test ../environment
	coverage run manage.py test -v 2
	coverage report
	npm run test:coverage

run_smoketests :
	python smoketests/smoke.py

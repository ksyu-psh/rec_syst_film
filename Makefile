redis:
	sudo docker run -p 6379:6379 -d redis
activate:
    python -m pipenv shell
beat:
	python -m celery -A tasks beat -l error --detach --logfile="./tmp/tmp.log" --pidfile="./tmp/tmp.pid"
worker:
	python -m celery -A tasks worker -n OKSANA -Q main_queue -l info -P solo
flower:
    python -m celery -A tasks.app flower
worker-d:
	python -m celery -A tasks worker -n OKSANA -Q main_queue -l error -P solo --detach --logfile="./tmp/tmp.log" --pidfile="./tmp/tmp.pid"
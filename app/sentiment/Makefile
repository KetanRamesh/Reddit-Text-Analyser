all : worker-sentiment 

worker-sentiment :
	docker build -f Dockerfile-sentiment -t docker-sentiment:2.0 .
	docker tag docker-sentiment:2.0 us.gcr.io/wired-rhino-267706/docker-sentiment:2.0
	docker push us.gcr.io/wired-rhino-267706/docker-sentiment:2.0
	kubectl apply -f sentiment-deployment.yaml

clean :
	docker rmi -f $(docker images -a -q)
	docker system prune -a
	docker rm $(docker ps -a -f status=exited -q)
all : worker-keywords

worker-keywords :
	docker build -f Dockerfile-keywords -t docker-keywords:2.0 .
	docker tag docker-keywords:2.0 us.gcr.io/wired-rhino-267706/docker-keywords:2.0
	docker push us.gcr.io/wired-rhino-267706/docker-keywords:2.0
	kubectl apply -f keywords-deployment.yaml

clean :
	docker rmi -f $(docker images -a -q)
	docker system prune -a
	docker rm $(docker ps -a -f status=exited -q)
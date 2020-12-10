all : worker-keywords

worker-keywords :
	docker build -f Dockerfile-keywords -t docker-keywords:1.0 .
	docker tag docker-keywords:1.0 us.gcr.io/datacenter-292401/docker-keywords:1.0
	docker push us.gcr.io/datacenter-292401/docker-keywords:1.0
	# kubectl apply -f keywords-deployment.yaml

clean :
	docker rmi -f $(docker images -a -q)
	docker system prune -a
	docker rm $(docker ps -a -f status=exited -q)
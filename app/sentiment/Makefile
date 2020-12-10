all : worker-sentiment 

worker-sentiment :
	docker build -f Dockerfile-sentiment -t docker-sentiment:1.0 .
	docker tag docker-sentiment:1.0 us.gcr.io/datacenter-292401/docker-sentiment:1.0
	docker push us.gcr.io/datacenter-292401/docker-sentiment:1.0
	# kubectl apply -f sentiment-deployment.yaml

clean :
	docker rmi -f $(docker images -a -q)
	docker system prune -a
	docker rm $(docker ps -a -f status=exited -q)
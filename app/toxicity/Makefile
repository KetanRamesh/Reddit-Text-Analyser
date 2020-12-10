all : worker-toxicity 

worker-toxicity :
	docker build -f Dockerfile-toxicity -t docker-toxicity:1.0 .
	docker tag docker-toxicity:1.0 us.gcr.io/datacenter-292401/docker-toxicity:1.0
	docker push us.gcr.io/datacenter-292401/docker-toxicity:1.0
	# kubectl apply -f toxicity-deployment.yaml

clean :
	docker rmi -f $(docker images -a -q)
	docker system prune -a
	docker rm $(docker ps -a -f status=exited -q)
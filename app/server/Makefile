all : rest-server

rest-server :
	docker build -f Dockerfile-server -t docker-server:2.0 .
	docker tag docker-server:2.0 us.gcr.io/datacenter-292401/docker-server:2.0
	docker push us.gcr.io/datacenter-292401/docker-server:2.0
	# kubectl apply -f server-deployment.yaml
	# kubectl apply -f server-service.yaml
	# kubectl apply -f server-ingress.yaml

clean :
	docker rmi -f $(docker images -a -q)
	docker system prune -a
	docker rm $(docker ps -a -f status=exited -q)
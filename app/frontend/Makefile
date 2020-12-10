all : frontend

frontend :
	docker build -f Dockerfile-frontend -t docker-frontend:3.0 .
	docker tag docker-frontend:3.0 us.gcr.io/datacenter-292401/docker-frontend:3.0
	docker push us.gcr.io/datacenter-292401/docker-frontend:3.0
	# kubectl apply -f frontend-deployment.yaml
	# kubectl apply -f frontend-service.yaml
	# kubectl apply -f frontend-ingress.yaml

clean :
	docker rmi -f $(docker images -a -q)
	docker system prune -a
	docker rm $(docker ps -a -f status=exited -q)
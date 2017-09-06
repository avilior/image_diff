# image_diff
A utility for comparing images
# Docker
Build and image: 
docker build -t image_diff .
Run the container:
docker run --rm -p 8080:80 --name image_diff image_diff
To use:
Launch a browser a go to http://localhost:8080/diff

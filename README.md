# image_diff
A utility for comparing images
# Docker
Build an image:
docker build -t compare_image .
Run the container:
docker run --rm -p 8080:80 --name compare_image compare_image
To use:
Launch a browser a go to http://localhost:8080/diff

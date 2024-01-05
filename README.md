# docker-flask-spotifyAPI
Dockerized Flask application utilizing the SpotifyAPI to get personalized music insights.

## Tech Stack

- python
- flask
- docker

## Setup

- create .env according to .env.template
- fill empty .env secrets
- build container
- run container

## Commands

- docker build -t {docker_tag_name} .
- docker images
- docker run -d -p 5000:5000 {docker_tag_name}
- docker ps
- docker stop {docker_id}
#!/bin/sh

cd "$(dirname "$0")"

docker build -t telcenter-core-ai-agent:1.0 .


docker run \
    --env-file=./.env.docker.local \
    telcenter-core-ai-agent:1.0

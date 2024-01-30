#!/bin/bash

docker exec -it mongocfg1 mongosh --eval 'rs.initiate({_id: "mongors1conf", configsvr: true, members: [{_id: 0, host: "mongocfg1"}, {_id: 1, host: "mongocfg2"}, {_id: 2, host: "mongocfg3"}]})'
sleep 10
docker exec -it mongocfg1 mongosh --eval 'rs.status()'

# first replic
docker exec -it mongors1n1 mongosh --eval 'rs.initiate({_id: "mongors1", members: [{_id: 0, host: "mongors1n1"}, {_id: 1, host: "mongors1n2"}, {_id: 2, host: "mongors1n3"}]})'
sleep 10
docker exec -it mongors1n1 mongosh --eval 'rs.status()'

docker exec -it mongos1 mongosh --eval 'sh.addShard("mongors1/mongors1n1")'
sleep 10

# second replic
docker exec -it mongors2n1 mongosh --eval 'rs.initiate({_id: "mongors2", members: [{_id: 0, host: "mongors2n1"}, {_id: 1, host: "mongors2n2"}, {_id: 2, host: "mongors2n3"}]})'
sleep 10

docker exec -it mongos1 mongosh --eval 'sh.addShard("mongors2/mongors2n1")'
sleep 10
docker exec -it mongos1 mongosh --eval 'sh.status()'

# Create DB, init sharding
docker exec -it mongos1 mongosh --eval 'use movies_ugc'
docker exec -it mongos1 mongosh --eval 'sh.enableSharding("movies_ugc")'
sleep 10

# Creating collection and sharing for it
docker exec -it mongos1 mongosh --eval 'db.createCollection("movies_ugc.ugc_events")'
docker exec -it mongos1 mongosh --eval 'sh.shardCollection("movies_ugc.ugc_events", {"user_id": "hashed"})'
# Проблема общей коллекции,- не у всех событий может быть film_id. Зато у всех есть user_id.
#docker exec -it mongos1 mongosh --eval 'sh.shardCollection("movies_ugc.ugc_events", {"film_id": "hashed"})'

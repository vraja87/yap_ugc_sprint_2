#!/bin/bash

docker exec -it mongocfg1 bash -c 'echo "rs.initiate({_id: \"mongors1conf\", configsvr: true, members: [{_id: 0, host: \"mongocfg1\"}, {_id: 1, host: \"mongocfg2\"}, {_id: 2, host: \"mongocfg3\"}]})" | mongosh'
sleep 10
docker exec -it mongocfg1 bash -c 'echo "rs.status()" | mongosh'

# first replic
docker exec -it mongors1n1 bash -c 'echo "rs.initiate({_id: \"mongors1\", members: [{_id: 0, host: \"mongors1n1\"}, {_id: 1, host: \"mongors1n2\"}, {_id: 2, host: \"mongors1n3\"}]})" | mongosh'
sleep 10
docker exec -it mongors1n1 bash -c 'echo "rs.status()" | mongosh'

docker exec -it mongos1 bash -c 'echo "sh.addShard(\"mongors1/mongors1n1\")" | mongosh'
sleep 10

# second replic
docker exec -it mongors2n1 bash -c 'echo "rs.initiate({_id: \"mongors2\", members: [{_id: 0, host: \"mongors2n1\"}, {_id: 1, host: \"mongors2n2\"}, {_id: 2, host: \"mongors2n3\"}]})" | mongosh'
sleep 10

docker exec -it mongos1 bash -c 'echo "sh.addShard(\"mongors2/mongors2n1\")" | mongosh'
sleep 10
docker exec -it mongos1 bash -c 'echo "sh.status()" | mongosh'

# Create DB, init sharding
docker exec -it mongos1 bash -c 'echo "use someDb" | mongosh'
docker exec -it mongos1 bash -c 'echo "sh.enableSharding(\"someDb\")" | mongosh'
sleep 10

# Создание коллекции и настройка шардинга для неё
docker exec -it mongos1 bash -c 'echo "db.createCollection(\"someDb.someCollection\")" | mongosh'
docker exec -it mongos1 bash -c 'echo "sh.shardCollection(\"someDb.someCollection\", {\"someField\": \"hashed\"})" | mongosh'

#!/bin/bash

./singularity_local.sh \
  -p ../yeastregulatorydb_sifs/yeastregulatorydb_production_postgres.sif \
  -r ../yeastregulatorydb_sifs/yeastregulatorydb_local_redis.sif \
  -d ../yeastregulatorydb_sifs/yeastregulatorydb_local_django.sif \
  -o ../yeastregulatorydb_sifs/yeastregulatorydb_local_docs.sif \
  -g ./postgres_data \
  -b ./backup \
  -v postgres_run \
  -t 3 \
  -s postgres,redis,django

# keep the job running
while true; do
  sleep 3600
done

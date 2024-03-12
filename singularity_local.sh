#!/bin/bash

# Function to check service readiness
check_service_ready() {
    local service_name=$1
    local check_command=$2
    local counter=0

    echo "Waiting for $service_name to start..."
    while ! eval $check_command; do
        if [ "$counter" -lt "$timeout_seconds" ]; then
            sleep 1
            ((counter++))
            echo "Checking $service_name... ($counter seconds)"
        else
            echo "Timeout reached. $service_name did not start within $timeout_minutes minutes."
            exit 1
        fi
    done
    echo "$service_name is up and running."
}

# Function to start each service
start_service() {
    case $1 in
        postgres)
            singularity run  --bind $postgres_data:/var/lib/postgresql/data \
                             --bind $postgres_run:/var/run/postgresql \
                             --bind $postgres_backup:/backups \
                             --env-file ./.envs/.local/.postgres $postgres_sif \
                             &>./postgres_log.txt &
            check_service_ready "PostgreSQL" "pg_isready -h localhost -p 5432"
            ;;
        redis)
            singularity exec $redis_sif redis-server &> redis_log.txt &
            check_service_ready "Redis" "redis-cli ping > /dev/null 2>&1"
            ;;
        django)
            singularity exec --bind .:/app \
                             --env-file ./.envs/.local/.concat_env_files \
                             $django_sif bash -c 'cd /app && /entrypoint /start' &> django_log.txt &
            check_service_ready "Django app" "curl -s http://localhost:8000 > /dev/null"
            ;;
        docs)
            singularity exec --bind .:/app \
                             --env-file ./.envs/.local/.django \
                             $docs_sif /start-docs &>docs_log.txt &
            check_service_ready "Docs" "echo 'Docs is ready'"
            ;;
        celeryworker)
            singularity exec --bind .:/app \
                             --env-file ./.envs/.local/.concat_env_files \
                             $django_sif /entrypoint /start-celeryworker &> celeryworker_log.txt &
            check_service_ready "Celery worker" "echo 'Celery worker is ready'"
            ;;
        celerybeat)
            singularity exec --bind .:/app \
                             --env-file ./.envs/.local/.concat_env_files \
                             $django_sif /entrypoint /start-celerybeat &> celerybeat_log.txt &
            check_service_ready "Celery beat" "echo 'Celery beat is ready'"
            ;;
        celeryflower)
            singularity exec --bind .:/app \
                             --env-file ./.envs/.local/.concat_env_files \
                             $django_sif /entrypoint /start-flower &> celeryflower_log.txt &
            check_service_ready "Celery flower" "echo 'Celery flower is ready'"
            ;;
        *)
            echo "Unknown service: $1"
            ;;
    esac
}

# Start specified services
for service in "${services_to_start[@]}"; do
    start_service $service
done

show_help() {
cat << EOF
Usage: ${0##*/} [OPTIONS]...
Launch Singularity containers for a Django application with optional services.

    -h, --help                          display this help and exit
    -p, --postgres_sif PATH             path to the PostgreSQL Singularity image file
    -r, --redis_sif PATH                path to the Redis Singularity image file
    -d, --django_sif PATH               path to the Django Singularity image file
    -o, --docs_sif PATH                 path to the Docs Singularity image file
    -g, --postgres_data PATH            path to the PostgreSQL data directory, eg postgres_data
    -b, --postgres_backup PATH          path to the PostgreSQL data backups directory, eg postgres_backup
    -v, --postgres_run PATH             path to the PostgresSQL run directory, eg postgres_run
    -t, --timeout MINUTES               optional timeout in minutes for service readiness checks (default: 3)
    -s, --services "SERVICE1 SERVICE2"  optional comma separated, no spaces, list of services to start (e.g., postgres,redis,django)

Examples:
    ${0##*/} -p /path/to/postgres.sif -r /path/to/redis.sif -d /path/to/django.sif -o /path/to/docs.sif \\
             -g /path/to/postgres_data -b /path/to/postgres_backup -v postgres_run /path/to/postgres_run \\
             -t 3 -s "postgres redis django"
EOF
}

# Initialize variables
postgres_sif=""
redis_sif=""
django_sif=""
docs_sif=""
postgres_data=postgres_data
postgres_backup=postgres_backup
postgres_run=postgres_run
timeout_minutes=3
services_to_start=()

# Parse options
OPTS=$(getopt -o hp:r:d:o:g:b:v:t:s: --long help,postgres_sif:,redis_sif:,django_sif:,docs_sif:,postgres_data:,postgres_backup:,postgres_run:,timeout:,services: -n 'parse-options' -- "$@")
if [ $? != 0 ] ; then echo "Failed parsing options." >&2 ; exit 1 ; fi

eval set -- "$OPTS"

while true; do
    case "$1" in
        -h | --help ) show_help; exit 0 ;;
        -p | --postgres_sif ) postgres_sif="$2"; shift 2 ;;
        -r | --redis_sif ) redis_sif="$2"; shift 2 ;;
        -d | --django_sif ) django_sif="$2"; shift 2 ;;
        -o | --docs_sif ) docs_sif="$2"; shift 2 ;;
        -g | --postgres_data ) postgres_data="$2"; shift 2 ;;
        -b | --postgres_backup ) postgres_backup="$2"; shift 2 ;;
        -v | --postgres_run ) postgres_run="$2"; shift 2 ;;
        -t | --timeout ) timeout_minutes="$2"; shift 2 ;;
        -s | --services )
            IFS=',' read -r -a services_to_start <<< "$2"
            shift 2 ;;
        -- ) shift; break ;;
        * ) break ;;
    esac
done

main() {
    # Loop over the array of packages to load them
    spack_packages=("postgresql" "singularityce" "redis")
    for pkg in "${spack_packages[@]}"; do
        if ! eval $(spack load --sh $pkg); then
            echo "Error loading $pkg package with spack. Ensure the package exists and is available."
            exit 1
        fi
        echo "$pkg loaded successfully."
    done

    let "timeout_seconds=timeout_minutes * 60"

    # Start specified services
    for service in "${services_to_start[@]}"; do
        start_service $service
    done
}

# Call main function
main "$@"

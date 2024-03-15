#!/bin/bash

set -e

# Declare an associative array to keep track of service PIDs
declare -A service_pids

# On EXIT from the script, kill the PID of the services
cleanup() {
    # Iterate over all PIDs and terminate them
    for pid in "${service_pids[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "Terminating service with PID $pid"
            kill -TERM "$pid"
        fi
    done
}

# Setup trap for cleanup on script exit
trap cleanup EXIT


# Function to check service readiness
# $1: service name
# $2: command to check service readiness
# Function to check service readiness
# Function to check service readiness
check_service_ready() {
    local service_name=$1
    local check_command=$2
    local counter=0
    local success=0

    echo "Waiting for $service_name to start. Will try for $timeout_seconds seconds..."

    while [ $counter -lt $timeout_seconds ]; do
        # Temporarily disable exit on error
        set +e
        eval $check_command
        if [ $? -eq 0 ]; then
            echo "$service_name is up and running."
            success=1
            break  # Exit the loop if service is ready
        else
            ((counter++))
            echo "Attempt $counter: Checking $service_name..."
            sleep 1
        fi
        # Re-enable exit on error
        set -e
    done

    if [ $success -ne 1 ]; then
        echo "Failed to start $service_name within $timeout_seconds seconds."
        exit 1
    fi
}


# Function to start each service
start_service() {
    # set the local sif_path variable based on the service
    local sif_path=""
    # instantiate the local variable `pid` to store process IDs
    local pid

    case $1 in
        postgres) sif_path="$POSTGRES_SIF" ;;
        redis) sif_path="$REDIS_SIF" ;;
        django) sif_path="$DJANGO_SIF" ;;
        docs) sif_path="$DOCS_SIF" ;;
        celeryworker) sif_path="$DJANGO_SIF" ;;
        celerybeat) sif_path="$DJANGO_SIF" ;;
        celeryflower) sif_path="$DJANGO_SIF" ;;
        *) echo "Unknown service: $1"; exit 1 ;;
    esac

    # check that the sif file exists
    if [ ! -e "$sif_path" ]; then
        echo "SIF file for $1 does not exist: $sif_path"
        exit 1
    fi

    # if the service is postgres, check if the postgres data, backup,
    # and run directories exist
    case $1 in
        postgres)
            if [ ! -d "$POSTGRES_DATA" ]; then
                echo "PostgreSQL data directory does not exist: $POSTGRES_DATA"
                exit 1
            fi
            if [ ! -d "$POSTGRES_BACKUP" ]; then
                echo "PostgreSQL backup directory does not exist: $POSTGRES_BACKUP"
                exit 1
            fi
            if [ ! -d "$POSTGRES_RUN" ]; then
                echo "PostgreSQL run directory does not exist: $POSTGRES_RUN"
                exit 1
            fi
            ;;
    esac

    # spack load the necessary packages based on the service
    case $1 in
        postgres)
            echo "trying to spack load postgresql..."
            if ! eval $(spack load --sh postgresql); then
                echo "Error loading PostgreSQL package with spack. Ensure the package exists and is available."
                exit 1
            fi
            echo "postgresql loaded successfully."
            ;;
        redis)
            echo "trying to spack load redis..."
            if ! eval $(spack load --sh redis); then
                echo "Error loading Redis package with spack. Ensure the package exists and is available."
                exit 1
            fi
            echo "redis loaded successfully."
            ;;
    esac

    # if $1 is not postgres or redis, check that the APP_CODEBASE exists
    if [ "$1" != "postgres" ] && [ "$1" != "redis" ]; then
        if [ ! -d "$APP_CODEBASE" ]; then
            echo "Application codebase does not exist: $APP_CODEBASE"
            exit 1
        fi
    fi

    # launch the service and check that it is running
    case $1 in
        postgres)
            singularity run  --bind $POSTGRES_DATA:/var/lib/postgresql/data \
                             --bind $POSTGRES_RUN:/var/run/postgresql \
                             --bind $POSTGRES_BACKUP:/backups \
                             --env-file $CONCAT_ENV_FILE $sif_path \
                             &>./postgres_log.txt &
            pid=$!
            check_service_ready "PostgreSQL" "pg_isready -h localhost -p 5432"
            service_pids[$1]=$pid
            ;;
        redis)
            singularity exec $sif_path redis-server &> redis_log.txt &
            pid=$!
            check_service_ready "Redis" "redis-cli ping > /dev/null 2>&1"
            service_pids[$1]=$pid
            ;;
        django)
            singularity exec --bind $APP_CODEBASE:/app \
                             --env-file $CONCAT_ENV_FILE \
                             $sif_path bash -c 'cd /app && /entrypoint /start' &> django_log.txt &
            pid=$!
            check_service_ready "Django app" "curl -s http://localhost:8000 > /dev/null"
            service_pids[$1]=$pid
            ;;
        docs)
            singularity exec --bind $APP_CODEBASE:/app \
                             --env-file $CONCAT_ENV_FILE \
                             $sif_path /start-docs &>docs_log.txt &
            pid=$!
            check_service_ready "Docs" "echo 'Docs is ready'"
            service_pids[$1]=$pid
            ;;
        celeryworker)
            singularity exec --bind $APP_CODEBASE:/app \
                             --env-file $CONCAT_ENV_FILE \
                             $sif_path bash -c 'cd /app && /entrypoint /start-celeryworker' &> celeryworker_log.txt &
            pid=$!
            check_service_ready "Celery worker" "echo 'Celery worker is ready'"
            service_pids[$1]=$pid
            ;;
        celerybeat)
            singularity exec --bind $APP_CODEBASE:/app \
                             --env-file $CONCAT_ENV_FILE \
                             $sif_path bash -c 'cd /app && /entrypoint /start-celerybeat' &> celerybeat_log.txt &
            pid=$!
            check_service_ready "Celery beat" "echo 'Celery beat is ready'"
            service_pids[$1]=$pid
            ;;
        celeryflower)
            singularity exec --bind $APP_CODEBASE:/app \
                             --env-file $CONCAT_ENV_FILE \
                             $sif_path bash -c 'cd /app && /entrypoint /start-flower' &> celeryflower_log.txt &
            pid=$!
            check_service_ready "Celery flower" "echo 'Celery flower is ready'"
            service_pids[$1]=$pid
            ;;
        *)
            echo "Unknown service: $1"
            exit 1
            ;;
    esac
}


show_help() {
cat << EOF
Usage: ${0##*/} [OPTIONS]...
Launch Singularity containers for a Django application with optional services. Note
that this assumes that postgresql, redis and singularityce can be loaded into the
environment with spack.

    -h, --help                          display this help and exit
    -c, --config PATH                   path to a bash variable assignment style
                                        configuration file. This file can set
                                        the following variables if not provided as command
                                        line arguments. If the variable is set both in
                                        the configuration file and on the cmd line,
                                        eg for postgres_host, the cmd line value will
                                        override the config file value.:
                                          - APP_CODEBASE: Path to the Django application codebase. This is bound into the container as /app.
                                          - CONCAT_ENV_FILE: Path to the concatenated environment file for the Django application.
                                          - POSTGRES_SIF: Path to the PostgreSQL Singularity image file.
                                          - REDIS_SIF: Path to the Redis Singularity image file.
                                          - DJANGO_SIF: Path to the Django Singularity image file.
                                          - DOCS_SIF: Path to the Docs Singularity image file.
                                          - POSTGRES_DATA: Path to the PostgreSQL data directory on the host to bind into the container.
                                          - POSTGRES_BACKUP: Path to the PostgreSQL backup directory on the host to bind into the container.
                                          - POSTGRES_RUN: Path to the PostgreSQL run directory on the host to bind into the container.
                                          - POSTGRES_HOST: IP address of the PostgreSQL host (default: localhost).
                                          - POSTGRES_PORT: Port of the PostgreSQL host (default: 5432).
                                          - REDIS_HOST: IP address of the Redis host (default: localhost).
                                          - REDIS_PORT: Port of the Redis host (default: 6379).
                                          - TIMEOUT_MINUTES: Timeout in minutes for service readiness checks (default: 3).

    -p, --postgres_host "192.83.21.1"   IP address of the PostgreSQL host. Defaults to localhost. Overrides configuration file value.
    --postgres_port "5432"              Port of the PostgreSQL host. Defaults to 5432. Overrides configuration file value.
    -r, --redis_host "192.84.21.1"      IP address of the Redis host. Defaults to localhost. Overrides configuration file value.
    --redis_port "6379"                 Port of the Redis host. Defaults to 6379. Overrides configuration file value.
    -t, --timeout MINUTES               Optional timeout in minutes for service readiness checks. Overrides configuration file value.
    -s, --services "SERVICE1 SERVICE2"  Comma-separated list of services to start (e.g., postgres,redis,django). Required.

Examples:
    ${0##*/} -c config.env -t 3 -s "postgres,redis,django"
EOF
}

# Initialize variables
CONFIG_FILE=""
APP_CODEBASE=""
CONCAT_ENV_FILE=""
POSTGRES_SIF=""
REDIS_SIF=""
DJANGO_SIF=""
DOCS_SIF=""
POSTGRES_DATA=""
POSTGRES_BACKUP=""
POSTGRES_RUN=""
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
REDIS_HOST=localhost
REDIS_PORT=6379
TIMEOUT_MINUTES=3
SERVICES_TO_START=()


main() {

    while true; do
        case "$1" in
            -h | --help ) show_help; exit 0 ;;
            -c | --config ) CONFIG_FILE="$2"; shift 2 ;;
            -p | --postgres_host ) POSTGRES_HOST="$2"; shift 2 ;;
            --postgres_port ) POSTGRES_PORT="$2"; shift 2 ;;
            -r | --redis_host ) REDIS_HOST="$2"; shift 2 ;;
            --redis_port ) REDIS_PORT="$2"; shift 2 ;;
            -t | --timeout ) TIMEOUT_MINUTES="$2"; shift 2 ;;
            -s | --services )
                IFS=',' read -r -a SERVICES_TO_START <<< "$2"
                shift 2 ;;
            -- ) shift; break ;;
            * ) break ;;
        esac
    done

    # confirm that the configuration file exists. If it does, source it
    if [ -e "$CONFIG_FILE" ]; then
        source "$CONFIG_FILE"
    else
        echo "Configuration file does not exist: $CONFIG_FILE"
        exit 1
    fi

    # Loop over the array of packages necessary to any service and try to load them
    spack_packages=("singularityce")
    for pkg in "${spack_packages[@]}"; do
        echo "trying to spack load $pkg..."
        if ! eval $(spack load --sh $pkg); then
            echo "Error loading $pkg package with spack. Ensure the package exists and is available."
            exit 1
        fi
        echo "$pkg loaded successfully."
    done

    let "timeout_seconds=TIMEOUT_MINUTES * 60"

    # Start specified services
    for service in "${SERVICES_TO_START[@]}"; do
        echo "attempting to start service: $service"
        start_service $service
    done

    # Keep script running indefinitely
    while true; do
        sleep 60
    done
}

# Parse options
OPTS=$(getopt -o h:c:p:r:t:s: --long help,config:,postgres_host:,postgres_port:,redis_host:,redis_port:,timeout:,services: -- "$@")
if [ $? != 0 ] ; then echo "Failed parsing options." >&2 ; exit 1 ; fi
eval set -- "$OPTS"

# Call main function
main "$@"

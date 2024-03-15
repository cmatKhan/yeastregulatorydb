#!/bin/bash

# Function to append messages to the log file
# $1: log message
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $log_file
}

# Function to extract the node name(s) allocated to a given Slurm job ID
get_slurm_job_nodename() {
    local job_id="$1"
    # Extract and filter NodeList, ignoring lines with (null) or ExcNodeList
    local node_list=$(scontrol show job "$job_id" | awk -F'=' '/NodeList=/ && !/ExcNodeList/ && !/\(null\)/ {print $2}')
    echo "$node_list"
}

# Function to print the help message
print_help() {
cat << EOF
Usage: ${0} [OPTIONS]
Launch Singularity containers for a Django application with optional services.

Options:
  --launch_script PATH               Specify the path to the launch script, eg singularity_local.sh.
  --config PATH                      Specify the path to the configuration file.
  --log_file PATH                    Specify the path to the log file (default: django_app_launch_log_<date>.txt).
  --postgres_cpus NUM                Number of CPUs for the PostgreSQL job (default: 2).
  --postgres_mem MEM                 Memory per CPU for the PostgreSQL job (default: 3G).
  --redis_cpus NUM                   Number of CPUs for the Redis job (default: 2).
  --redis_mem MEM                    Memory per CPU for the Redis job (default: 3G).
  --django_cpus NUM                  Number of CPUs for the Django job (default: 2).
  --django_mem MEM                   Memory per CPU for the Django job (default: 3G).
  --celeryworker_cpus NUM            Number of CPUs for the Celery Worker job (default: 2).
  --celeryworker_mem MEM             Memory per CPU for the Celery Worker job (default: 3G).
  -h, --help                         Display this help message and exit.

Example:
  ${0} --launch_script ./singularity_local.sh --config /path/to/config.env
EOF
}

# Initialize default values before processing options
launch_script=""
config_file=""
log_file="django_app_launch_log_$(date '+%Y-%m-%d').txt"
postgres_cpus=2
postgres_mem="3G"
redis_cpus=2
redis_mem="3G"
django_cpus=2
django_mem="3G"
celeryworker_cpus=2
celeryworker_mem="3G"

while true; do
    case "$1" in
        --launch_script ) launch_script="$2"; shift 2 ;;
        --config ) config_file="$2"; shift 2 ;;
        --log_file ) log_file="$2"; shift 2 ;;
        --postgres_cpus ) postgres_cpus="$2"; shift 2 ;;
        --postgres_mem ) postgres_mem="$2"; shift 2 ;;
        --redis_cpus ) redis_cpus="$2"; shift 2 ;;
        --redis_mem ) redis_mem="$2"; shift 2 ;;
        --django_cpus ) django_cpus="$2"; shift 2 ;;
        --django_mem ) django_mem="$2"; shift 2 ;;
        --celeryworker_cpus ) celeryworker_cpus="$2"; shift 2 ;;
        --celeryworker_mem ) celeryworker_mem="$2"; shift 2 ;;
        -h | --help ) print_help; exit 0 ;;
        -- ) shift; break ;;
        * ) break ;;
    esac
done

main () {

    # check that launch_script exists
    if [ ! -e "$launch_script" ]; then
        echo "Error: launch_script not found: $launch_script" >&2
        exit 1
    fi

    # check that config_file exists
    if [ ! -e "$config_file" ]; then
        echo "Error: config_file not found: $config_file" >&2
        exit 1
    fi

    log "Submitting PostgreSQL job with CPUs: $postgres_cpus, Memory: $postgres_mem"
    postgres_job_id=$(
    sbatch -c "$postgres_cpus" --mem-per-cpu="$postgres_mem" \
            $launch_script -c "$config_file" -s postgres \
    | cut -d ' ' -f 4
    )
    log "PostgreSQL job submitted with ID: $postgres_job_id"

    log "Submitting redis job with CPUs: $redis_cpus, Memory: $redis_mem"
    redis_job_id=$(
    sbatch -c "$redis_cpus" --mem-per-cpu="$redis_mem" \
            $launch_script -c "$config_file" -s redis \
    | cut -d ' ' -f 4
    )
    log "PostgreSQL job submitted with ID: $redis_job_id"

    # Wait for the node names
    postgres_host=$(get_slurm_job_nodename "$postgres_job_id")
    log "PostgreSQL running on host: $postgres_host, Port: ${POSTGRES_PORT:-5432}"

    redis_host=$(get_slurm_job_nodename "$redis_job_id")
    log "Redis running on host: $redis_host, Port: ${REDIS_PORT:-6379}"

    # launch django via sbatch. However, this depends on postgres and redis
    # log "Submitting Django job with CPUs: $django_cpus, Memory: $django_mem"
    # django_job_id=$(sbatch \
    #     -c "$django_cpus" \
    #     --mem-per-cpu="$django_mem" \
    #     --dependency=afterok:$postgres_job_id:$redis_job_id \
    #     $launch_script \
    #     -c "$config_file" \
    #     --postgres_host "$postgres_host" \
    #     --redis_host "$redis_host" \
    #     -s django | cut -d ' ' -f 4)
    # log "Django job submitted with dependency on PostgreSQL and Redis. Job ID: $django_job_id"


}

# Parse options
OPTS=$(getopt -o h --long launch_script:,config:,log_file:,postgres_cpus:,postgres_mem:,redis_cpus:,redis_mem:,django_cpus:,django_mem:,celeryworker_cpus:,celeryworker_mem:,help -- "$@")
if [ $? != 0 ] ; then echo "Failed parsing options." >&2 ; exit 1 ; fi
eval set -- "$OPTS"

main "$@"

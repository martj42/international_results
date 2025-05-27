#!/usr/bin/env zsh

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME=""
IMAGE_NAME=""
SCRIPT_DIR="$(cd "$(dirname "${(%):-%N}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ENGINE="podman"  # Default engine

# Functions
function log_info() {
    echo -e "${GREEN}>> ShellScript::${FUNCNAME[1]} $1${NC}"
}

function log_warn() {
    echo -e "${YELLOW}>>> ShellScript::${FUNCNAME[1]} $1${NC}"
}

function log_error() {
    echo -e "${RED}>>>> ShellScript::${FUNCNAME[1]} $1${NC}"
}

function parse_arguments() {
    # Parse command line arguments
    CONTAINER_ARGS=()
    RESTART_FLAG=false

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --container-name|-cn)
                CONTAINER_NAME="$2"
                log_info "Using container name: $CONTAINER_NAME"
                shift 2
                ;;
            --image-name|-in)
                IMAGE_NAME="$2"
                log_info "Using image name: $IMAGE_NAME"
                shift 2
                ;;
            --engine|-e)
                ENGINE="$2"
                log_info "Using container engine: $ENGINE"
                shift 2
                ;;
            --restart|-r)
                log_info "Restart flag enabled - will restart container if it exists"
                RESTART_FLAG=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --container-name, -cn NAME   Set container name (mandatory)"
                echo "  --image-name, -in NAME       Set image name (mandatory)"
                echo "  --engine, -e ENGINE          Set container engine (podman or docker, default: podman)"
                echo "  --restart, -r                Restart container if it exists (without this flag, exits if container exists)"
                echo "  --help, -h                   Show this help message"
                exit 0
                ;;
            *)
                log_info "Passing additional argument to container: $1"
                CONTAINER_ARGS+=("$1")
                shift
                ;;
        esac
    done

    # Check for mandatory parameters
    if [[ -z "$CONTAINER_NAME" ]]; then
        log_error "Missing mandatory parameter: --container-name or -cn"
        exit 1
    fi
    if [[ -z "$IMAGE_NAME" ]]; then
        log_error "Missing mandatory parameter: --image-name or -in"
        exit 1
    fi
}

function check_dependencies() {
    log_info "Checking dependencies"

    # Check if engine is installed
    if ! command -v $ENGINE &> /dev/null; then
        log_error "$ENGINE is not installed. Please install $ENGINE to continue."
        exit 1
    fi

    # Check if image exists
    if ! $ENGINE image inspect "${IMAGE_NAME}" &> /dev/null; then
        log_error "Image ${IMAGE_NAME} does not exist. Please build it first with: $ENGINE build -t ${IMAGE_NAME} -f ${PROJECT_ROOT}/container/Dockerfile.dev ${PROJECT_ROOT}"
        exit 1
    fi
}

function check_existing_container() {
    log_info "Checking for existing container"

    # Check if container already exists (regardless of state)
    if $ENGINE container inspect "${CONTAINER_NAME}" &> /dev/null; then
        # Container exists (running or stopped)
        if [ "$RESTART_FLAG" = true ]; then
            # If container is running, stop it first
            if $ENGINE ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
                log_warn "Container ${CONTAINER_NAME} is running - will stop and remove it due to --restart flag"
                $ENGINE stop "${CONTAINER_NAME}"
            else
                log_warn "Container ${CONTAINER_NAME} exists but is not running - will remove it due to --restart flag"
            fi

            # Remove the container
            $ENGINE rm "${CONTAINER_NAME}"
            log_info "Container ${CONTAINER_NAME} removed"
        else
            # No restart flag, exit with warning
            log_warn "Container ${CONTAINER_NAME} already exists (running or stopped)"
            log_warn "Use --restart or -r flag to remove the existing container and create a new one"
            log_info "Exiting without starting a new container"
            exit 0
        fi
    else
        # No existing container, --restart flag has no effect
        log_info "No existing container found"
    fi
}

function run_container() {
    log_info "Starting container ${CONTAINER_NAME}"

    container_cmd="$ENGINE run -d -it \
        --name \"${CONTAINER_NAME}\" \
        -v \"${PROJECT_ROOT}/:/app/:Z\" \
        -e \"BASE_PATH=/app\" \
        \"${IMAGE_NAME}\""

    # Add any additional arguments to pass to the entrypoint
    if [[ ${#CONTAINER_ARGS[@]} -gt 0 ]]; then
        log_info "Passing arguments to container entrypoint: ${CONTAINER_ARGS[*]}"
        for arg in "${CONTAINER_ARGS[@]}"; do
            container_cmd+=" $arg"
        done
    fi

    # Execute the container command
    eval ${container_cmd}

    if [ $? -ne 0 ]; then
        log_error "Failed to start container"
        exit 1
    fi

    log_info "Container ${CONTAINER_NAME} started successfully"
}

# Main execution
function main() {
    log_info "Starting knowledge container setup"

    # Parse command line arguments
    parse_arguments "$@"

    # Check for dependencies
    check_dependencies

    # Check for existing container
    check_existing_container

    # Run the container
    run_container

    log_info "Container setup completed"
}

# Call the main function with all arguments
main "$@"
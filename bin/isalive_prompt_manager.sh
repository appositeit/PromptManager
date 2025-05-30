#!/bin/bash
# Script to check if the Prompt Manager server is alive

PORT="8095"
TIMEOUT=10 # Default timeout in seconds

# Parse command-line arguments
while getopts ":p:t:" opt; do
  case ${opt} in
    p )
      PORT=$OPTARG
      ;;
    t )
      TIMEOUT=$OPTARG
      ;;
    \? )
      echo "Usage: $0 [-p PORT] [-t TIMEOUT_SECONDS]" 1>&2
      exit 1
      ;;
    : )
      echo "Invalid option: -$OPTARG requires an argument" 1>&2
      exit 1
      ;;
  esac
done
shift $((OPTIND -1))

# Prefer a dedicated health check endpoint if available, otherwise use /api/prompts/all
HEALTH_ENDPOINT="http://0.0.0.0:$PORT/api/prompts/all"

echo "Checking server status at $HEALTH_ENDPOINT for up to $TIMEOUT seconds..."

START_TIME=$(date +%s)

while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED_TIME=$((CURRENT_TIME - START_TIME))

    if [ "$ELAPSED_TIME" -ge "$TIMEOUT" ]; then
        echo "Timeout: Server did not respond correctly at $HEALTH_ENDPOINT within $TIMEOUT seconds."
        exit 1
    fi

    # -L to follow redirects, --fail to fail silently on server errors (HTTP 4xx, 5xx)
    HTTP_CODE=$(curl -L --fail -s -o /dev/null -w "%{http_code}" "$HEALTH_ENDPOINT")
    CURL_EXIT_CODE=$?

    if [ "$CURL_EXIT_CODE" -eq 0 ] && [ "$HTTP_CODE" -eq 200 ]; then
        echo "Server is alive. (HTTP $HTTP_CODE after $ELAPSED_TIME seconds)"
        exit 0
    elif [ "$CURL_EXIT_CODE" -eq 22 ]; then # curl error 22 is HTTP page not retrieved (4xx/5xx)
        echo "Attempt $((ELAPSED_TIME + 1))/$TIMEOUT: Server responded with HTTP $HTTP_CODE. Retrying..."
    elif [ "$CURL_EXIT_CODE" -ne 0 ]; then # Other curl errors (e.g., 7 for connection refused)
        echo "Attempt $((ELAPSED_TIME + 1))/$TIMEOUT: Connection failed (curl code $CURL_EXIT_CODE). Retrying..."
    else # HTTP code not 200, but curl exit code 0 (should not happen with --fail typically)
        echo "Attempt $((ELAPSED_TIME + 1))/$TIMEOUT: Server not ready (HTTP $HTTP_CODE, curl code $CURL_EXIT_CODE). Retrying..."
    fi
    
    sleep 1
done 

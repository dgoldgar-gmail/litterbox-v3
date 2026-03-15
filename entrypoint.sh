#!/bin/bash

export MODE=${MODE:-manager}

if [ "$MODE" = "satellite" ]; then
    echo "Configuring environment for SATELLITE mode..."
    #export START_WEB="false"
    export START_ANSIBLE="false"
    export APP_MODE="API"

else
    echo "Configuring environment for MANAGER mode..."
    #export START_WEB="true"
    export START_ANSIBLE="true"
    export APP_MODE="FULL"
fi

exec "$@"
#! /bin/bash

curl --location --request POST 'https://agent-coordinator-5zz5xno5ma-ew.a.run.app/invoke' \
    --header 'Content-Type: application/json' \
    --header "Authorization: Bearer $(gcloud auth print-identity-token)" \
    --data-raw '{
        "input": {
            "message": "What is Google Cloud?",
            "session_id": "1234567890"
        }
    }'

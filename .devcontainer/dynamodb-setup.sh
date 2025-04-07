#!/bin/bash
# This script creates the necessary DynamoDB tables for development

# Wait for DynamoDB to be fully available
echo "Waiting for DynamoDB Local to start..."
sleep 5

# Create the RockPaperScissor_Games table
echo "Creating RockPaperScissor_Games table..."
aws dynamodb create-table \
    --endpoint-url http://dynamodb-local:8000 \
    --table-name RockPaperScissor_Games \
    --attribute-definitions \
        AttributeName=game_id,AttributeType=S \
        AttributeName=user_id,AttributeType=S \
        AttributeName=session_id,AttributeType=S \
    --key-schema \
        AttributeName=game_id,KeyType=HASH \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --global-secondary-indexes \
        "[
            {
                \"IndexName\": \"UserIndex\",
                \"KeySchema\": [{\"AttributeName\":\"user_id\",\"KeyType\":\"HASH\"}],
                \"Projection\": {\"ProjectionType\":\"ALL\"},
                \"ProvisionedThroughput\": {\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}
            },
            {
                \"IndexName\": \"SessionIndex\",
                \"KeySchema\": [{\"AttributeName\":\"session_id\",\"KeyType\":\"HASH\"}],
                \"Projection\": {\"ProjectionType\":\"ALL\"},
                \"ProvisionedThroughput\": {\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}
            }
        ]"

echo "DynamoDB setup complete!"
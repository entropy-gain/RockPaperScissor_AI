"""
Database connection module for RockPaperScissor game.
Provides connectivity to DynamoDB, either in AWS or local development environment.
"""
import boto3
import os
import logging
import time
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

def get_dynamodb_resource():
    """
    Get a DynamoDB resource with appropriate configuration based on environment
    
    Returns:
        boto3.resource: Configured DynamoDB resource
    """
    try:
        # Check if in production AWS environment
        if os.environ.get('AWS_ENV') == 'production':
            # AWS environment
            return boto3.resource('dynamodb')
        else:
            # Local development environment
            return boto3.resource(
                'dynamodb',
                endpoint_url='http://localhost:8001',  # Standard port is 8000
                region_name='us-east-1',
                aws_access_key_id='dummy',
                aws_secret_access_key='dummy'
            )
    
    except Exception as e:
        logger.error(f"Error creating DynamoDB resource: {str(e)}")
        raise

def get_dynamodb_client():
    """
    Get a DynamoDB client with appropriate configuration based on environment
    
    Returns:
        boto3.client: Configured DynamoDB client
    """
    try:
        # Check if in production AWS environment
        if os.environ.get('AWS_ENV') == 'production':
            # AWS environment
            return boto3.client('dynamodb')
        else:
            # Local development environment
            return boto3.client(
                'dynamodb',
                endpoint_url='http://localhost:8001',  # Standard port is 8000
                region_name='us-east-1',
                aws_access_key_id='dummy',
                aws_secret_access_key='dummy'
            )
    
    except Exception as e:
        logger.error(f"Error creating DynamoDB client: {str(e)}")
        raise

def wait_for_table_creation(client, table_name):
    """
    Wait for a table to be created
    
    Args:
        client: DynamoDB client
        table_name: Name of the table to wait for
        
    Returns:
        bool: True if table created successfully
    """
    retries = 0
    max_retries = 10
    while retries < max_retries:
        try:
            response = client.describe_table(TableName=table_name)
            table_status = response['Table']['TableStatus']
            if table_status == 'ACTIVE':
                logger.info(f"Table {table_name} is now active")
                return True
            logger.info(f"Waiting for table {table_name} to be created. Current status: {table_status}")
            time.sleep(3)
            retries += 1
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.warning(f"Table {table_name} not found yet. Waiting...")
                time.sleep(3)
                retries += 1
            else:
                logger.error(f"Error checking table status: {str(e)}")
                return False
    
    logger.error(f"Timed out waiting for table {table_name} to be created")
    return False

def create_tables_if_not_exist():
    """
    Create required DynamoDB tables if they don't exist
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        client = get_dynamodb_client()
        existing_tables = client.list_tables()['TableNames']
        
        # Create Games table if it doesn't exist
        if 'RockPaperScissor_Games' not in existing_tables:
            client.create_table(
                TableName='RockPaperScissor_Games',
                KeySchema=[
                    {'AttributeName': 'game_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'game_id', 'AttributeType': 'S'},
                    {'AttributeName': 'user_id', 'AttributeType': 'S'},
                    {'AttributeName': 'session_id', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'UserIndex',
                        'KeySchema': [
                            {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    },
                    {
                        'IndexName': 'SessionIndex',
                        'KeySchema': [
                            {'AttributeName': 'session_id', 'KeyType': 'HASH'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            logger.info("Creating RockPaperScissor_Games table...")
            success = wait_for_table_creation(client, 'RockPaperScissor_Games')
            if success:
                logger.info("RockPaperScissor_Games table created successfully")
                return True
            else:
                logger.error("Failed to create RockPaperScissor_Games table")
                return False
        else:
            logger.info("RockPaperScissor_Games table already exists")
            return True
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceInUseException':
            logger.warning(f"Table already exists: {str(e)}")
            return True
        else:
            logger.error(f"Error creating tables: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"Unexpected error creating tables: {str(e)}")
        return False
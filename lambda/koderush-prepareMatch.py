import json
import boto3
from dynamo_manager import DynamoMatchManager

dynamodb = boto3.resource('dynamodb')
dynamodb_client = boto3.client('dynamodb')
api_client = boto3.client('apigatewaymanagementapi', endpoint_url="https://ngkia3mb99.execute-api.us-east-1.amazonaws.com/production")

def get_request_data(event):
    return event["requestContext"]["connectionId"], json.loads(event["body"])

def send_message(connection_id, data):
    return api_client.post_to_connection(
        ConnectionId=connection_id,
        Data=json.dumps(data).encode('utf-8')  # Ensure binary encoding
    )

def create_table_if_not_exists(name, key_schema, attr_defs):
    try:
        dynamodb_client.create_table(
            TableName=name,
            KeySchema=key_schema,
            AttributeDefinitions=attr_defs,
            BillingMode="PAY_PER_REQUEST"
        )
    except dynamodb_client.exceptions.ResourceInUseException:
        pass  # Already exists

def lambda_handler(event, context):
    connection_id, body = get_request_data(event)
    match_id = body.get("matchId")

    if not match_id:
        return {"statusCode": 400, "body": "Missing matchId"}

    manager = DynamoMatchManager(match_id)
    
    try:
        manager.create_temp_tables()

        metadata = manager.get_match_metadata()
        if not metadata:
            send_message(connection_id, {"message": "Match not found"})
            return {"statusCode": 404, "body": "No match metadata"}

        send_message(connection_id, {
            "message": "Match prepared",
            "matchMetadata": metadata
        })
        return {"statusCode": 200}
    except Exception as e:
        send_message(connection_id, {"message": f"Error: {str(e)}"})
        return {"statusCode": 500, "body": f"Error: {str(e)}"}

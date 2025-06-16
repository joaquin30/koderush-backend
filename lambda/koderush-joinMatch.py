import json
import boto3

client = boto3.client('apigatewaymanagementapi', endpoint_url="https://ngkia3mb99.execute-api.us-east-1.amazonaws.com/production")

def get_request_data(event):
    return event["requestContext"]["connectionId"], json.loads(event["body"])

def send_message(connection_id, data):
    return client.post_to_connection(
        ConnectionId=connection_id,
        Data=json.dumps(data)
    )

# Function that lambda will run (keep name as it is)
def lambda_handler(event, context):
    print("Received event:", json.dumps(event))
    
    connection_id, eventBody = get_request_data(event)
    match_id = eventBody["matchId"]
    player_name = eventBody['playerName']

    data = {"matchId": match_id, "playerName": player_name}
    send_message(connection_id, data)

    return {"statusCode": 200}

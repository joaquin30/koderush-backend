import json
import boto3

dynamodb_client = boto3.client('dynamodb')
api_client = boto3.client('apigatewaymanagementapi', endpoint_url="https://ngkia3mb99.execute-api.us-east-1.amazonaws.com/production")

def get_request_data(event):
    return event["requestContext"]["connectionId"], json.loads(event["body"])

def send_message(connection_id, data):
    return api_client.post_to_connection(
        ConnectionId=connection_id,
        Data=json.dumps(data)
    )

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))

    try:
        connection_id, eventBody = get_request_data(event)
        match_id = eventBody["matchId"]
        if not match_id:
            return {"statusCode": 400, "body": "Missing matchId"}

        # Define table names
        players_table = f"tempPlayers_{match_id}"
        problems_table = f"tempPlayerProblems_{match_id}"
        tutorials_table = f"tempPlayerTutorials_{match_id}"

        # Create tempPlayers table
        dynamodb_client.create_table(
            TableName=players_table,
            KeySchema=[
                {"AttributeName": "connectionId", "KeyType": "HASH"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "connectionId", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST"
        )

        # Create tempPlayerProblems table
        dynamodb_client.create_table(
            TableName=problems_table,
            KeySchema=[
                {"AttributeName": "player", "KeyType": "HASH"},
                {"AttributeName": "problemId", "KeyType": "RANGE"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "player", "AttributeType": "S"},
                {"AttributeName": "problemId", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST"
        )

        # Create tempPlayerTutorials table
        dynamodb_client.create_table(
            TableName=tutorials_table,
            KeySchema=[
                {"AttributeName": "player", "KeyType": "HASH"},
                {"AttributeName": "tutorialId", "KeyType": "RANGE"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "player", "AttributeType": "S"},
                {"AttributeName": "tutorialId", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST"
        )

        send_message(connection_id, {"message": "Tables created successfully"})
        return {"statusCode": 200} # This is for the API, not for the connected user

    except dynamodb_client.exceptions.ResourceInUseException as e:
        send_message(connection_id, {"message": f"One or more tables already exist: {str(e)}"})
        return {
            "statusCode": 400,
            "body": f"One or more tables already exist: {str(e)}"
        }
    except Exception as e:
        send_message(connection_id, {"message": f"Error: {str(e)}"})
        return {
            "statusCode": 500,
            "body": f"Error: {str(e)}"
        }

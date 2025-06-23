from dynamo_manager import DynamoMatchManager
from api_manager import ApiManager
from rds_manager import RDSManager

api_manager = ApiManager()
rds_manager = RDSManager()

def lambda_handler(event, context):
    connection_id, body = api_manager.get_request_data(event)
    match_id = body.get("match_id")

    if not match_id:
        api_manager.send_message(connection_id, {"message": 'invalid_match'})
        return {"statusCode": 404, "body": "Match ID not provided"}
    
    dynamo_manager = DynamoMatchManager(match_id)

    if not dynamo_manager.check_table_exists():
        api_manager.send_message(connection_id, {"message": 'invalid_match'})
        return {"statusCode": 404, "body": "No active match found"}
    
    try:
        connection_ids = dynamo_manager.get_connection_ids()

        if not connection_ids:
            api_manager.send_message(connection_id, {"message": "No players found"})
            return {"statusCode": 404, "body": "No players found in the match"}

        for player_connection_id in  connection_ids:
            data = {"message": "match_ended", "match_id": match_id}
            api_manager.send_message(player_connection_id, data)

        data = {"message": "match_ended", "match_id": match_id}
        api_manager.send_message(connection_id, data)
        return {"statusCode": 200, "body": "Match ended successfully"}
    except Exception as e:
        print(f"Error retrieving connection IDs: {e}")
        api_manager.send_message(connection_id, {"message": "Error retrieving connection IDs"})
        return {"statusCode": 500, "body": "Error retrieving connection IDs"}
    
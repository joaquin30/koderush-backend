from dynamo_manager import DynamoMatchManager
from api_manager import ApiManager
from rds_manager import RDSManager

api_manager = ApiManager()
rds_manager = RDSManager()

def lambda_handler(event, context):
    connection_id, body = api_manager.get_request_data(event)
    match_id = body.get("match_id")

    if not match_id:
        api_manager.send_message(connection_id, {"message": "Match not found"})
        return {"statusCode": 404, "body": "No active match found"}
    
    dynamo_manager = DynamoMatchManager(match_id)

    if not dynamo_manager.check_table_exists():
        api_manager.send_message(connection_id, {"message": "Match not found"})
        return {"statusCode": 404, "body": "No active match found"}
    
    try:
        connection_ids = dynamo_manager.get_connection_ids()
        if not connection_ids:
            api_manager.send_message(connection_id, {"message": "No players found"})
            return {"statusCode": 404, "body": "No players found in the match"}
        data = {"message": "start_timestamp", "connection_ids": connection_ids}
        api_manager.send_message(connection_id, data)
    except Exception as e:
        print(f"Error retrieving connection IDs: {e}")
        api_manager.send_message(connection_id, {"message": "Error retrieving connection IDs"})
        return {"statusCode": 500, "body": "Error retrieving connection IDs"}
    
    # TODO: ..., just finished until returning the connection IDs of the players in the match to the API client
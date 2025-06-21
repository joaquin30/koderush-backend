from dynamo_manager import DynamoMatchManager
from api_manager import ApiManager
from rds_manager import RDSManager

api_manager = ApiManager()
rds_manager = RDSManager()

def lambda_handler(event, context):
    connection_id, body = api_manager.get_request_data(event)
    match_id = body.get("matchId")

    if not match_id:
        api_manager.send_message(connection_id, {"message": "Match not found"})
        return {"statusCode": 404, "body": "No match found"}
    
    status, records = rds_manager.execute_statement(
        "SELECT match_id FROM matches WHERE match_id = :match_id",
        parameters=[{"name": "match_id", "value": {"stringValue": match_id}}]
    )

    if status != 200 or not records:
        api_manager.send_message(connection_id, {"message": "Match not found"})
        return {"statusCode": 404, "body": "No match found"}

    dynamo_manager = DynamoMatchManager(match_id)
    
    try:
        dynamo_manager.create_temp_tables()

        api_manager.send_message(connection_id, {
            "message": "Match prepared"
        })
        return {"statusCode": 200, "body": "Temp tables successfully"}
    except Exception as e:
        api_manager.send_message(connection_id, {"message": f"Error while creating tables: {str(e)}"})
        return {"statusCode": 500, "body": f"Error while creating tables: {str(e)}"}

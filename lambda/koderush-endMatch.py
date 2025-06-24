from dynamo_manager import DynamoMatchManager
from api_manager import ApiManager
from rds_manager import RDSManager
import boto3

api_manager = ApiManager()
rds_manager = RDSManager()

def cleanup_end_event(match_id):
    rule_name = f"end-match-{match_id}"
    events = boto3.client('events')

    try:
        events.remove_targets(Rule=rule_name, Ids=['1'])
        events.delete_rule(Name=rule_name)
        print(f"Cleaned up EventBridge rule and target for match {match_id}")
        return True
    except Exception as e:
        print(f"Error cleaning up rule for match {match_id}: {e}")
        return False

def lambda_handler(event, context):
    match_id = event.get("match_id")

    if not match_id:
        print("Match ID not provided in event by eventBridge.")
        return {"statusCode": 404, "body": "Match ID not provided"}
    
    dynamo_manager = DynamoMatchManager(match_id)

    if not dynamo_manager.check_table_exists():
        print(f"No active match found for match_id={match_id}")
        return {"statusCode": 404, "body": "No active match found"}
    
    try:
        connection_ids = dynamo_manager.get_connection_ids()

        if not connection_ids:
            print(f"No players found in match {match_id}")
            return {"statusCode": 404, "body": "No players found in the match"}

        for player_connection_id in  connection_ids:
            data = {"message": "match_ended", "match_id": match_id}
            api_manager.send_message(player_connection_id, data)

        cleanup_end_event(match_id)
        return {"statusCode": 200, "body": "Match ended successfully"}
    except Exception as e:
        print(f"Error ending match {match_id}: {e}")
        return {"statusCode": 500, "body": "Error while ending match"}
    
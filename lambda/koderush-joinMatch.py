from dynamo_manager import DynamoMatchManager
from api_manager import ApiManager
from rds_manager import RDSManager

api_manager = ApiManager()
rds_manager = RDSManager()

# Function that lambda will run (keep name as it is)
def lambda_handler(event, context):
    connection_id, body = api_manager.get_request_data(event)
    match_id = body.get("match_id")
    player = body.get("player")

    if not match_id:
        api_manager.send_message(connection_id, {"message": "Match not found"})
        return {"statusCode": 404, "body": "No active match found"}
    
    dynamo_manager = DynamoMatchManager(match_id)

    if not dynamo_manager.check_table_exists():
        api_manager.send_message(connection_id, {"message": "Match not found"})
        return {"statusCode": 404, "body": "No active match found"}

    # TODO: Handle the case when the match has already started ...

    try:
        player_connection_ids = dynamo_manager.get_connection_ids()
        
        for player_connection_id in player_connection_ids:
            data = {"message": "new_player", "player": player}
            api_manager.send_message(player_connection_id, data) # Before actually adding the player

        dynamo_manager.add_player(player, connection_id)

        players = dynamo_manager.get_players()
        state = rds_manager.get_player_state(match_id, player, players, dynamo_manager)
        data = {"message": "state_update", "state": state}
        api_manager.send_message(connection_id, data)

        return {"statusCode": 200, "body": "Player added successfully"}
    except Exception as e:
        print(f"Error adding player: {e}")
        api_manager.send_message(connection_id, {"message": "Error adding player"})
        return {"statusCode": 500, "body": "Error adding player"}
    
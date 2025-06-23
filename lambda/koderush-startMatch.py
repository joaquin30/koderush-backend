from dynamo_manager import DynamoMatchManager
from api_manager import ApiManager
from rds_manager import RDSManager
import time

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
        players = dynamo_manager.get_players()
        connection_ids = dynamo_manager.get_connection_ids()
        problems = rds_manager.get_problems(match_id)

        if not connection_ids:
            api_manager.send_message(connection_id, {"message": "No players found"})
            return {"statusCode": 404, "body": "No players found in the match"}
        
        rds_manager.set_start_timestamp(match_id, int(time.time()))
        state = {}

        print(f'{match_id} started with players: {players}')
        for i in range(len(players)):
            player = players[i]
            player_connection_id = connection_ids[i]
            for problem_id in problems.keys():
                dynamo_manager.add_problem_access(player, problem_id)
                dynamo_manager.add_tutorial_access(player, problem_id)

            # I think that the only thing that chnages in the state is the player    
            if i == 0:
                print('Calculated state for the first time')
                state = rds_manager.get_player_state(match_id, player, players, dynamo_manager)
            
            state['player'] = player
            data = {"message": "state_update", "state": state}
            api_manager.send_message(player_connection_id, data)

        data = {"message": "match_started", "match_id": match_id}
        api_manager.send_message(connection_id, data)
        return {"statusCode": 200, "body": "Match started successfully"}
    except Exception as e:
        print(f"Error retrieving connection IDs: {e}")
        api_manager.send_message(connection_id, {"message": "Error retrieving connection IDs"})
        return {"statusCode": 500, "body": "Error retrieving connection IDs"}
    
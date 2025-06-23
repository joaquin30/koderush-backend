from dynamo_manager import DynamoMatchManager
from api_manager import ApiManager
from rds_manager import RDSManager
from piston_manager import PistonManager
import time

api_manager = ApiManager()
rds_manager = RDSManager()
coderunner = PistonManager()

def lambda_handler(event, context):
    connection_id, body = api_manager.get_request_data(event)
    match_id = body.get("match_id")
    player = body.get("player")
    problem_id = body.get("problem_id")
    language = body.get("language")
    solution = body.get("solution")
    timestamp = int(time.time())

    if not match_id:
        api_manager.send_message(connection_id, {"message": "Match not found"})
        return {"statusCode": 404, "body": "No matchID was provided"}
    
    dynamo_manager = DynamoMatchManager(match_id)

    if not dynamo_manager.check_table_exists():
        api_manager.send_message(connection_id, {"message": "Match not found"})
        return {"statusCode": 404, "body": "No active match found"}
    
    problems = rds_manager.get_problems(problem_id)
    problem = problems.get(problem_id)
    
    if not problem:
        api_manager.send_message(connection_id, {"message": "Problem not found"})
        return {"statusCode": 404, "body": "Problem not found"}
    
    veredict = coderunner.validate_solution(problem, solution, language)

    done = rds_manager.add_player_submission(match_id, player, problem_id, language, solution, timestamp, veredict)
    if not done:
        api_manager.send_message(connection_id, {"message": "Error uploading solution"})
        return {"statusCode": 500, "body": "Error uploading solution"}
    
    connection_ids = dynamo_manager.get_connection_ids()
    players = dynamo_manager.get_players()
    if not connection_ids:
        api_manager.send_message(connection_id, {"message": "No players connected"})
        return {"statusCode": 404, "body": "No players connected"}
    
    state = {}

    print(f'{match_id} started with players: {players}')
    for i in range(len(players)):
        player = players[i]
        player_connection_id = connection_ids[i]

        # I think that the only thing that chnages in the state is the player    
        if i == 0:
            print('Calculated state for the first time')
            state = rds_manager.get_player_state(match_id, player, players, dynamo_manager)
            
        state['player'] = player
        data = {"message": "state_update", "state": state}
        api_manager.send_message(player_connection_id, data)

    api_manager.send_message(connection_id, {"message": "new_submission", "connection_ids": connection_ids})
    return {"statusCode": 200, "body": "Solution uploaded successfully"}
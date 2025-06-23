from dynamo_manager import DynamoMatchManager
from api_manager import ApiManager
from rds_manager import RDSManager
from piston_manager import PistonManager

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
    timestamp = body.get("timestamp")

    if not match_id:
        api_manager.send_message(connection_id, {"message": "Match not found"})
        return {"statusCode": 404, "body": "No active match found"}
    
    dynamo_manager = DynamoMatchManager(match_id)

    if not dynamo_manager.check_table_exists():
        api_manager.send_message(connection_id, {"message": "Match not found"})
        return {"statusCode": 404, "body": "No active match found"}
    
    problem = dynamo_manager.get_problem_by_id(problem_id)
    
    if not problem:
        api_manager.send_message(connection_id, {"message": "Problem not found"})
        return {"statusCode": 404, "body": "Problem not found"}
    
    veredict = coderunner.validate_solution(problem, solution, language)

    #match_id, player, problem_id, language, solution, timestamp, veredict
    done = rds_manager.add_player_submission(match_id, player, problem_id, language, solution, timestamp, veredict) # TODO
    if not done:
        api_manager.send_message(connection_id, {"message": "Error uploading solution"})
        return {"statusCode": 500, "body": "Error uploading solution"}
    api_manager.send_message(connection_id, {"message": "Solution uploaded successfully", "veredict": veredict})
    return {"statusCode": 200, "body": "Solution uploaded successfully"}
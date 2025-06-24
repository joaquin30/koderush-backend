from dynamo_manager import DynamoMatchManager
from api_manager import ApiManager
from rds_manager import RDSManager
import time
import boto3
import json
import os
from datetime import datetime, timedelta

api_manager = ApiManager()
rds_manager = RDSManager()

def get_cron_expression(minutes):
    """Generate a cron expression for a one-time event."""
    now = datetime.utcnow()
    target_time = now + timedelta(minutes=minutes)
    print(f"Scheduling for {target_time} UTC")
    return f"cron({target_time.minute} {target_time.hour} {target_time.day} {target_time.month} ? *)"

def create_end_event(match_id, delay_minutes=5):
    events = boto3.client('events')
    lambda_client = boto3.client('lambda')

    # Compute the time to invoke the Lambda
    schedule_time = get_cron_expression(delay_minutes)
    print(f"Scheduling end event for match {match_id} with cron expression: {schedule_time}")

    rule_name = f"end-match-{match_id}"

    # Create one-time rule
    response = events.put_rule(
        Name=rule_name,
        ScheduleExpression=schedule_time,
        State='ENABLED'
    )
    rule_arn = response['RuleArn']

    # Target Lambda ARN from env var
    target_lambda_arn = os.environ['END_LAMBDA_ARN']

    # Add permission for EventBridge to invoke target Lambda
    try:
        lambda_client.add_permission(
            FunctionName=target_lambda_arn,
            StatementId=f"{rule_name}-invoke",
            Action='lambda:InvokeFunction',
            Principal='events.amazonaws.com',
            SourceArn=rule_arn
        )
    except lambda_client.exceptions.ResourceConflictException:
        # Permission already exists
        pass

    # Set the target with match_id as input
    events.put_targets(
        Rule=rule_name,
        Targets=[
            {
                'Id': '1',
                'Arn': target_lambda_arn,
                'Input': json.dumps({'match_id': match_id})
            }
        ]
    )

    print(f"Scheduled match end event for {match_id} at {schedule_time}")
    return True

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
        match_info = rds_manager.get_match(match_id)

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
        end_delay = int(match_info["seconds_per_problem"])/60 * len(problems)
        print(f"Scheduling end event for match {match_id} in {end_delay} minutes")
        create_end_event(match_id, delay_minutes=1) # For testing for now
        return {"statusCode": 200, "body": "Match started successfully"}
    except Exception as e:
        print(f"Error retrieving connection IDs: {e}")
        api_manager.send_message(connection_id, {"message": "Error retrieving connection IDs"})
        return {"statusCode": 500, "body": "Error retrieving connection IDs"}
    
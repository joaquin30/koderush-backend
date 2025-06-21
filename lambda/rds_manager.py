import boto3
import os

class RDSManager:
    def __init__(self):
        self.cluster_arn = os.environ['CLUSTER_ARN']
        self.secret_arn = os.environ['CLUSTER_SECRET_ARN']
        self.database = os.environ['DB_NAME']
        self.rds_client = boto3.client('rds-data')

    # There could be a problem with the start_timestamp (returned true instead of NULL)
    def format_rds_records(self, records, table_name):
        # Define schemas for supported tables
        table_schemas = {
            "problem_examples": [
                "example_id", "problem_id", "input", "output", "explanation", "is_public"
            ],
            "problems": [
                "problem_id", "title", "memory_limit", "time_limit",
                "statement", "input_description", "output_description", "tutorial"
            ],
            "submissions": [
                "submission_id", "match_id", "player", "problem_id",
                "language", "solution", "timestamp", "veredict"
            ],
            "matches": [
                "match_id", "start_timestamp", "seconds_per_problem", "seconds_per_tutorial"
            ],
            "match_problems": [
                "match_id", "problem_id"
            ]
        }

        if table_name not in table_schemas:
            raise ValueError(f"Unsupported table name: {table_name}")

        column_names = table_schemas[table_name]
        formatted_records = []

        for row in records:
            record = {}
            for col_name, value_obj in zip(column_names, row):
                # Extract the value regardless of its type
                value = next(iter(value_obj.values()))
                record[col_name] = value
            formatted_records.append(record)

        return formatted_records

    # Returns the status code and formatted records if any. -1 status code indicates an error while executing the query.
    def execute_statement(self, query, table_name, parameters=None):
        try:
            response = self.rds_client.execute_statement(
                resourceArn=self.cluster_arn,
                secretArn=self.secret_arn,
                database=self.database,
                parameters=parameters or [],
                sql=query
            )
            status = response.get('ResponseMetadata', {}).get('HTTPStatusCode', 200)
            records = response.get('records', [])
            return status, self.format_rds_records(records, table_name)
        except Exception as e:
            print(f"Error executing SQL: {e}")
            return -1, None
        
    def get_players_submissions(self, match_id):
        # TODO: ...
        return []
    
    # TODO: Complete this function for the whole state (missing submissions and problems logic)
    def get_player_state(self, match_id, player, players):
        
        matches_query = """
            SELECT * FROM matches
            WHERE match_id = :match_id;
        """
        status, matches_data = self.execute_statement(matches_query, "matches", [{"name": "match_id", "value": {"stringValue": match_id}}])

        if status != 200 or not matches_data:
            print(f"Error fetching match data for match_id {match_id}")
            return None

        player_state = {
            'match_id': match_id,
            'start_timestamp': matches_data[0]["start_timestamp"],
            'seconds_per_problem': matches_data[0]["seconds_per_problem"],
            'seconds_per_tutorial': matches_data[0]["seconds_per_tutorial"],
            'player': player,
            'players': players,
            'problem_count': 0, # TODO
            'problems': {},
            'submissions': self.get_players_submissions(match_id)
        }

        return player_state
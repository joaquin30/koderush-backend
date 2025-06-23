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
        
    def set_start_timestamp(self, match_id, start_timestamp):
        update_query = """
            UPDATE matches
            SET start_timestamp = :start_timestamp
            WHERE match_id = :match_id;
        """
        parameters = [
            {"name": "start_timestamp", "value": {"longValue": start_timestamp}},
            {"name": "match_id", "value": {"stringValue": match_id}}
        ]
        status, _ = self.execute_statement(update_query, "matches", parameters)
        if status != 200:
            print(f"Error updating start timestamp for match_id {match_id}")
            return False
        return True
        
    def get_problems(self, match_id):
        problems_query = """
            SELECT p.problem_id, p.title, p.memory_limit, p.time_limit,
                   p.statement, p.input_description, p.output_description, p.tutorial
            FROM problems p
            JOIN match_problems mp ON p.problem_id = mp.problem_id
            WHERE mp.match_id = :match_id;
        """
        status, problems_data = self.execute_statement(problems_query, "problems", [{"name": "match_id", "value": {"stringValue": match_id}}])

        problems = {}

        if status != 200 or not problems_data:
            print(f"Error fetching problems for match_id {match_id}")
            return []
        
        print(f"Problems data for match_id {match_id}: {problems_data}")
        
        for problem in problems_data:
            examples_query = """
                SELECT *
                FROM problem_examples
                WHERE problem_id = :problem_id;
            """
            status, examples_data = self.execute_statement(examples_query, "problem_examples", [{"name": "problem_id", "value": {"stringValue": problem["problem_id"]}}])
            
            if status != 200 or not examples_data:
                print(f"Error fetching examples for problem_id {problem['problem_id']}")
                problem['examples'] = []
            else:
                examples_list = []
                for example_row in examples_data:
                    examples_list.append({
                        'example_id': example_row['example_id'],
                        'input': example_row['input'],
                        'output': example_row['output'],
                        'explanation': example_row['explanation'],
                        'is_public': bool(example_row['is_public'])
                    })

                problems[problem['problem_id']] = {
                    'problem_id': problem['problem_id'],
                    'title': problem['title'],
                    'memory_limit': problem['memory_limit'],
                    'time_limit': problem['time_limit'],
                    'statement': problem['statement'],
                    'input_description': problem['input_description'],
                    'output_description': problem['output_description'],
                    'tutorial': problem['tutorial'],
                    'examples': examples_list
                }

        return problems
        
    def get_players_submissions(self, match_id):
        submissions_query = """
            SELECT *
                FROM submissions
            WHERE match_id = :match_id;
        """
        status, submissions_data = self.execute_statement(submissions_query, "submissions", [{"name": "match_id", "value": {"stringValue": match_id}}])
        if status != 200:
            print(f"Error fetching submissions for match_id {match_id}")
            return []
        elif not submissions_data:
            print(f"No submissions found for match_id {match_id}")
            return []
        return [{
            'player': row['player'],
            'problem_id': row['problem_id'],
            'timestamp': row['timestamp'],
            'veredict': row['veredict'],
        } for row in submissions_data]
    
    def add_player_submission(self, match_id, player, problem_id, language, solution, timestamp, veredict):
        insert_query = """
            INSERT INTO submissions (match_id, player, problem_id, language, solution, timestamp, veredict)
            VALUES (:match_id, :player, :problem_id, :language, :solution, :timestamp, :veredict);  
        """
        parameters = [
            {"name": "match_id", "value": {"stringValue": match_id}},
            {"name": "player", "value": {"stringValue": player}},
            {"name": "problem_id", "value": {"stringValue": problem_id}},
            {"name": "language", "value": {"stringValue": language}},
            {"name": "solution", "value": {"stringValue": solution}},
            {"name": "timestamp", "value": {"intValue": timestamp}},
            {"name": "veredict", "value": {"stringValue": veredict}}
        ]
        status, _ = self.execute_statement(insert_query, "submissions", parameters)
        if status != 200:
            print(f"Error adding submission for match_id {match_id}, player {player}, problem_id {problem_id}")
            return False
        return True
    
    def get_player_state(self, match_id, player, players, dynamo_manager):
        
        matches_query = """
            SELECT * FROM matches
            WHERE match_id = :match_id;
        """
        status, matches_data = self.execute_statement(matches_query, "matches", [{"name": "match_id", "value": {"stringValue": match_id}}])

        if status != 200 or not matches_data:
            print(f"Error fetching match data for match_id {match_id}")
            return None
        
        problems = self.get_problems(match_id)

        player_state = {
            'match_id': match_id,
            'start_timestamp': matches_data[0]["start_timestamp"],
            'seconds_per_problem': matches_data[0]["seconds_per_problem"],
            'seconds_per_tutorial': matches_data[0]["seconds_per_tutorial"],
            'player': player,
            'players': players,
            'problem_count': len(problems),
            'problems': {},
            'submissions': self.get_players_submissions(match_id)
        }

        print(f"Player state for {player} in match {match_id}: {player_state}")

        for problem_id, problem in problems.items():
            if dynamo_manager.check_problem_access(player, problem_id):
                problem_data = dict(problem)
                problem_data['examples'] = list(filter(lambda x: x['is_public'], problem_data['examples']))
                if not dynamo_manager.check_tutorial_access(player, problem_id):
                    problem_data['tutorial'] = None
                player_state['problems'][problem_id] = problem_data
            else:
                player_state['problems'][problem_id] = None

        return player_state
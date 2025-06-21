import boto3
from botocore.exceptions import ClientError

class DynamoMatchManager:
    def __init__(self, match_id):
        self.match_id = str(match_id)
        self.dynamodb = boto3.resource("dynamodb")
        self.client = boto3.client("dynamodb")
        
        self.players_table_name = f"tempPlayers_{self.match_id}"
        self.problems_table_name = f"tempPlayerProblems_{self.match_id}"
        self.tutorials_table_name = f"tempPlayerTutorials_{self.match_id}"

    def _create_table_if_not_exists(self, name, key_schema, attr_defs):
        try:
            self.client.create_table(
                TableName=name,
                KeySchema=key_schema,
                AttributeDefinitions=attr_defs,
                BillingMode="PAY_PER_REQUEST"
            )
        except self.client.exceptions.ResourceInUseException:
            pass

    def create_temp_tables(self):
        self._create_table_if_not_exists(
            self.players_table_name,
            [
                {"AttributeName": "player", "KeyType": "HASH"},
                {"AttributeName": "connectionId", "KeyType": "RANGE"}
            ],
            [
                {"AttributeName": "player", "AttributeType": "S"},
                {"AttributeName": "connectionId", "AttributeType": "S"}
            ]
        )

        self._create_table_if_not_exists(
            self.problems_table_name,
            [
                {"AttributeName": "player", "KeyType": "HASH"},
                {"AttributeName": "problemId", "KeyType": "RANGE"}
            ],
            [
                {"AttributeName": "player", "AttributeType": "S"},
                {"AttributeName": "problemId", "AttributeType": "S"}
            ]
        )

        self._create_table_if_not_exists(
            self.tutorials_table_name,
            [
                {"AttributeName": "player", "KeyType": "HASH"},
                {"AttributeName": "tutorialId", "KeyType": "RANGE"}
            ],
            [
                {"AttributeName": "player", "AttributeType": "S"},
                {"AttributeName": "tutorialId", "AttributeType": "S"}
            ]
        )

    def add_player(self, player_id, connection_id):
        table = self.dynamodb.Table(self.players_table_name)
        try:
            table.put_item(Item={"player": player_id, "connectionId": connection_id})
        except ClientError as e:
            print(f"Error adding player: {e}")

    def check_player(self, player_id):
        table = self.dynamodb.Table(self.players_table_name)
        response = table.get_item(Key={"player": player_id})
        return "Item" in response
    
    def check_table_exists(self, table_name=None):
        if table_name is None:
            table_name = self.players_table_name
        try:
            self.client.describe_table(TableName=table_name)
            return True
        except self.client.exceptions.ResourceNotFoundException:
            return False

    def add_problem_access(self, player_id, problem_id):
        table = self.dynamodb.Table(self.problems_table_name)
        try:
            table.put_item(Item={"player": player_id, "problemId": problem_id})
        except ClientError as e:
            print(f"Error adding problem access: {e}")

    def check_problem_access(self, player_id, problem_id):
        table = self.dynamodb.Table(self.problems_table_name)
        response = table.get_item(Key={"player": player_id, "problemId": problem_id})
        return "Item" in response

    def add_tutorial_access(self, player_id, tutorial_id):
        table = self.dynamodb.Table(self.tutorials_table_name)
        try:
            table.put_item(Item={"player": player_id, "tutorialId": tutorial_id})
        except ClientError as e:
            print(f"Error adding tutorial access: {e}")

    def check_tutorial_access(self, player_id, tutorial_id):
        table = self.dynamodb.Table(self.tutorials_table_name)
        response = table.get_item(Key={"player": player_id, "tutorialId": tutorial_id})
        return "Item" in response
    
    def get_players(self):
        table = self.dynamodb.Table(self.players_table_name)
        response = table.scan()
        return [item['player'] for item in response.get('Items', [])]

import json
import boto3
import os

class ApiManager:
    def __init__(self):
        self.endpoint_url = os.environ.get('API_ENDPOINT_URL', None)
        self.api_client = boto3.client('apigatewaymanagementapi', endpoint_url=self.endpoint_url)

    def get_request_data(self, event):
        return event["requestContext"]["connectionId"], json.loads(event["body"])

    def send_message(self, connection_id, data):
        return self.api_client.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(data).encode('utf-8')  # Ensure binary encoding
        )
    
from api_manager import ApiManager
from rds_manager import RDSManager

api_manager = ApiManager()
rds_manager = RDSManager()

# Function that lambda will run (keep name as it is)
def lambda_handler(event, context):
    connection_id, body = api_manager.get_request_data(event)
    type = body.get("type")
    metadata = body.get("data")

    if not metadata:
        api_manager.send_message(connection_id, {"message": "Data was not sent"})
        return {"statusCode": 404, "body": "Data was not provided"}

    # TODO: Handle the case when the match has already started ...

    try:
        success = rds_manager.insert_data(type, metadata)
        
        if success:
            print(f"Data inserted successfully: {metadata}")
            data = {"message": "Data inserted"}
            api_manager.send_message(connection_id, data)
            return {"statusCode": 200, "body": "Data inserted successfully"}

        print(f"Failed to insert data: {metadata}")
        return {"statusCode": 500, "body": "Data insertion failed"}
    except Exception as e:
        print(f"Error adding player: {e}")
        api_manager.send_message(connection_id, {"message": "Error inserting data"})
        return {"statusCode": 500, "body": "Error inserting data"}
    
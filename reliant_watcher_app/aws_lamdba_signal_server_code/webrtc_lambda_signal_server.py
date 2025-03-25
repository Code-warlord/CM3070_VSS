# This code is designed to run as an AWS Lambda function,
# serving as a WebRTC signaling server to route data between
# the web interface and the Reliant Watcher Smart_VSS.


import json
import boto3

bucket_name = "reliant-watcher-webrtc-signal-server-storage"
vss_file_key = "vss_connection_id.json"
web_file_key = "web_interface_connection_id.json"
s3_client = boto3.client('s3')
connections_URL = 'https://gjtxmivc5m.execute-api.us-east-1.amazonaws.com/production'
api_gateway_client = boto3.client('apigatewaymanagementapi', endpoint_url=connections_URL)

def get_connection_id(file_key):
    try:
        s3_obj = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        s3_obj_content = s3_obj['Body'].read().decode('utf-8')
        connection_id = json.loads(s3_obj_content)['connection_id']
        return connection_id
    except Exception as e:
        print(f"Error retrieving connection ID: {e}")
        return None

def webrtc_signal_server(event, context):
    request_context = event['requestContext']
    if request_context['routeKey'] == "$default":
        body = json.loads(event['body'])
        if body["step"] == "1_connect":
            connection_id = request_context['connectionId']
            data = {"id": body['id'], "connection_id": connection_id} 
            if body['id'] == "smart_vss":
                s3_client.put_object(Bucket=bucket_name, Key=vss_file_key, Body= json.dumps(data), ContentType='application/json')
                data["step"] = body["step"]
                return {"statusCode": 200,"body": json.dumps(data)}
            elif body['id'] == "web_interface":
                s3_client.put_object(Bucket=bucket_name, Key=web_file_key, Body=json.dumps(data), ContentType='application/json')
                data["step"] = body["step"]
                if get_connection_id(vss_file_key) is None:
                    data["error"] = "vss not ready"
                else:
                    try:
                        api_gateway_client.post_to_connection(ConnectionId=get_connection_id(vss_file_key), Data=json.dumps(data))
                    except api_gateway_client.exceptions.GoneException:
                        data["error"] = "vss ready disconnected due to lost of internet access, try again in 10 minutes"
                return {"statusCode": 200, "body": json.dumps(data)}
            else:
                try:
                    # Call delete_connection to disconnect the client
                    api_gateway_client.delete_connection(ConnectionId=connection_id)
                    print(f'Successfully disconnected connection ID: {connection_id}')
                except api_gateway_client.exceptions.GoneException:
                    print(f'Connection ID {connection_id} is already disconnected.')
                return {"statusCode": 403, "body": "unauthorised connection"}
            
        elif body["step"] == "2_send_offer":
            data = json.dumps({"step": body["step"], "offer": body['offer']})
            #send offer to other user
            api_gateway_client.post_to_connection(ConnectionId=get_connection_id(vss_file_key), Data=data)
            return {"statusCode": 200,"body": data}

        elif body["step"] == "3_send_offer_ice":
            data = json.dumps({"step": body["step"], "ice_candidate": body['ice_candidate']})
            #send offer to other user
            api_gateway_client.post_to_connection(ConnectionId=get_connection_id(vss_file_key), Data=data)
            return {"statusCode": 200,"body": data}

        elif body["step"] == "4_send_answer":
            data = json.dumps({"step": body["step"], "answer": body['answer']})
            #send answer to other user
            api_gateway_client.post_to_connection(ConnectionId=get_connection_id(web_file_key), Data=data)
            return {"statusCode": 200,"body": data}

    elif request_context['routeKey'] == "$disconnect":
        if request_context['connectionId'] == get_connection_id(web_file_key):
            data = json.dumps({"step": "5_disconnect"})
            api_gateway_client.post_to_connection(ConnectionId=get_connection_id(vss_file_key), Data=data)
import json
import boto3

import datetime
import requests
from requests_aws4auth import AWS4Auth

from elasticsearch import Elasticsearch, RequestsHttpConnection

def get_metadata(bucket, image):
    client = boto3.client('s3')
    response = client.head_object(
        Bucket=bucket,
        Key=image,
    )
    
    # TODO : Parse metadata from user
    # print(response['ResponseMetadata']['HTTPHeaders']['last-modified'])
    # create
    # print("Response: ", response)
    metadata_labels = []
    # created_timestamp = ''
    # return created_timestamp, metadata_labels
    return metadata_labels
    
def connect_rekognition(bucket, photo):
    client=boto3.client('rekognition')

    # process using S3 object
    response = client.detect_labels(Image={'S3Object': {'Bucket': bucket, 'Name': photo}},
        MaxLabels= 8, MinConfidence = 75)    
    # Get the custom labels
    labels_data=response['Labels']
    labels = []
    for label_data in labels_data:
        labels.append(label_data['Name'])
    print("Labels from recognition: ", labels)
    return labels

def get_required_info(event):
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    image_name = event['Records'][0]['s3']['object']['key']
    print("Bucket Name: ", bucket_name)
    print("Image Name:", image_name)
    return bucket_name, image_name

def send_to_es(bucket, image, labels):
    es = Elasticsearch(
        hosts=[{'host': 'search-photos3-wrhauukzuqwxqu4vuq7bixrdda.us-east-1.es.amazonaws.com', 'port': 443}],
        http_auth=('hariharanjaya', 'Harirockz1!'),
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )

    dataObject = {
        'objectKey' : image,
        'bucket' : bucket,
        'createdTimestamp' : str(datetime.datetime.now().isoformat()), #TODO : check if sending this is fine
        'labels' : labels
    }
    
    rep = es.index(
        index="photos3",
        doc_type="_doc",
        id=image + bucket,
        body=dataObject,
        refresh=True)
        
    print(rep)
    """
    dataObject = {
        'objectKey' : image,
        'bucket' : bucket,
        'createdTimestamp' : str(datetime.datetime.now().isoformat()), #TODO : check if sending this is fine
        'labels' : labels
    }
    
    url = 'https://search-photos3-wrhauukzuqwxqu4vuq7bixrdda.us-east-1.es.amazonaws.com/photos3/_doc'
    
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, 'us-east-1', 'es', session_token=credentials.token)
    headers = {"Content-Type" : "application/json"}
    
    response = requests.post(url, auth=awsauth, headers = headers, data = json.dumps(dataObject))
    print(response)
    """
    
def lambda_handler(event, context):
    # get bucket and image
    bucket, image = get_required_info(event)
    
    # get required labels
    labels = connect_rekognition(bucket, image)
    metadata_labels = get_metadata(bucket, image)
    combined_labels = labels
    for label in metadata_labels:
        combined_labels.extend(label)
    
    # write to ES
    send_to_es(bucket, image, combined_labels)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }


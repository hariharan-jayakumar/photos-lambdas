import json
import boto3

import inflect
import datetime
import requests
from requests_aws4auth import AWS4Auth

from elasticsearch import Elasticsearch, RequestsHttpConnection

#adding comment

def get_metadata(bucket, image):
    service = boto3.resource('s3')
    """response = client.head_object(
        Bucket=bucket,
        Key=image,
    )"""
    object = service.Object(bucket, image)

    print(json.dumps(object.metadata))
    metadata_labels = []
    if "customlabels" in object.metadata:
        custom_labels = object.metadata['customlabels'].split(',')
        metadata_labels.extend(custom_labels)
    # TODO : Parse metadata from user
    # print(response['ResponseMetadata']['HTTPHeaders']['last-modified'])
    # create
    # print("Response: ", response)
    
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

def remove_plural(word):
    check = inflect.engine().singular_noun(word)
    return word if check is False else check
    
def send_to_es(bucket, image, labels):
    es = Elasticsearch(
        hosts=[{'host': 'search-photos-es4ieoq6di4xg3e2xhu5mcbumq.us-east-1.es.amazonaws.com', 'port': 443}],
        http_auth=('hariharanjaya', 'Harirockz1!'),
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )

    dataObject = {
        'objectKey' : image,
        'bucket' : bucket,
        'createdTimestamp' : str(datetime.datetime.now().isoformat()),
        'labels' : labels
    }
    
    rep = es.index(
        index="photos",
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
    print(event)
    bucket, image = get_required_info(event)
    
    # get required labels
    labels = connect_rekognition(bucket, image)
    metadata_labels = get_metadata(bucket, image)
    
    print(labels)
    print(metadata_labels)
    
    combined_labels = labels
    
    for label in metadata_labels:
        combined_labels.append(label)
        
    combined_labels = [remove_plural(label) for label in combined_labels]
    
    # write to ES
    send_to_es(bucket, image, combined_labels)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

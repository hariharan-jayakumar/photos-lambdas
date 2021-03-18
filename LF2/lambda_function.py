import json
import requests
import boto3
from requests_aws4auth import AWS4Auth

def search_elastic_search(queries):
    region = 'us-east-1'  # For example, us-west-1
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

    headers = {"Content-Type": "application/json"}
    query = {
        "query" : {
            "match" : {
                "labels" : "outdoor"
            }
        }
    }
    url = 'https://search-photos3-wrhauukzuqwxqu4vuq7bixrdda.us-east-1.es.amazonaws.com/photos3/_search/'

    r = requests.get(url, auth=("hariharanjaya", "Harirockz1!"), headers=headers, data=json.dumps(query))
    
    print("r = ",r)
    r_dict = json.loads(r.text)
    result_list = r_dict["hits"]["hits"]
    image_url_list = []

    response = {}
    response["results"] = []
    if result_list is not None:
        for result in result_list:
            response_object = {}
            s3_url = "https://" + result["_source"]["bucket"] + ".s3.amazonaws.com/" + result["_source"]["objectKey"]
            response_object["url"] = s3_url
            response_object["labels"] = result["_source"]["labels"]
            response["results"].append(response_object)

    print(response)
    """
    queries = "flowers"
    headers = {}
    print('Searching ElasticSearch domain')
    url = "https://search-photos3-wrhauukzuqwxqu4vuq7bixrdda.us-east-1.es.amazonaws.com/_search?size=1&&q=" + queries
    response = requests.get(url, headers=headers, auth=("hariharanjaya", "Harirockz1!")).json()
    restaurants = response['hits']['hits']
    """

def search(intent_request):
    slots = intent_request['currentIntent']['slots']
    search_items = ""
    for key, value in slots.items():
        if value is not None:
            print(value)
            search_items += value + " "
    
    print("Search queries", search_items)
    
    response_es = search_elastic_search("")
    response = {
        'statusCode': 200,
        'headers': {
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        },
        'body': json.dumps(response_es)
    }
    """response = {
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": "Fulfilled",
            "message": {
              "contentType": "SSML",
              "content": "Searching for " + search_items
            },
        }
    }"""
    return response

def lambda_handler(event, context):
    print(event)
    intent_name = event['currentIntent']['name']
    
    if intent_name == 'SearchIntent':
        return search(event)
        
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

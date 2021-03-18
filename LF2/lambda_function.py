import json
import requests
import boto3
from requests_aws4auth import AWS4Auth

def search_elastic_search(es_queries):
    region = 'us-east-1'  # For example, us-west-1
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

    headers = {"Content-Type": "application/json"}
    query = {
        "query" : {
            "match" : {
                "labels" : es_queries
            }
        }
    }
    url = 'https://search-photos3-wrhauukzuqwxqu4vuq7bixrdda.us-east-1.es.amazonaws.com/photos3/_search/'

    r = requests.get(url, auth=("hariharanjaya", "Harirockz1!"), headers=headers, data=json.dumps(query))
    
    
    print("r = ",r)
    
    r_dict = json.loads(r.text)
    return r_dict

def get_search_query(intent_request):
    slots = intent_request['slots']
    search_items = ""
    for key, value in slots.items():
        if value is not None:
            print(value)
            search_items += value + " "
    
    print("Search queries", search_items)
    
    return search_items

def lambda_handler(event, context):
    print(event)
    
    client = boto3.client('lex-runtime')
    
    # 'queryStringParameters': {'query': 'red'}
    response = client.post_text(
        botName='PhotoSearch',
        botAlias='photo_lex',
        userId='User1',
        inputText=event['queryStringParameters']['query']
    )
    
    print(response)
    
    search_query = get_search_query(response)
    response_es = search_elastic_search(search_query)
    
    print(response_es)

    results = []
    for hit in response_es['hits']['hits']:
        result = 'https://photos-bucket-assignment2.s3.amazonaws.com/' + hit["_source"]["objectKey"]
        results.append(result)

    print(results)
    response_to_return = {
        'statusCode': 200,
        'headers': {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        'body': list(set(results))
    }
    print(response_to_return)
    return response_to_return
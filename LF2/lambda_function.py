import json
import requests
import boto3
import inflect
from requests_aws4auth import AWS4Auth


def remove_plural(word):
    check = inflect.engine().singular_noun(word)
    return word if check is False else check

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
    
    url = 'https://search-photos-es4ieoq6di4xg3e2xhu5mcbumq.us-east-1.es.amazonaws.com/photos/_search/'

    r = requests.get(url, auth=("hariharanjaya", "Harirockz1!"), headers=headers, data=json.dumps(query))
    
    
    print("r = ",r)
    
    r_dict = json.loads(r.text)
    return r_dict

def get_search_query(intent_request):
    slots = intent_request['slots']
    search_items = []
    for key, value in slots.items():
        if value is not None:
            value = remove_plural(value)
            print(value)
            search_items.append(value)
    
    search_items = " OR ".join(search_items)
    
    print("Search queries", search_items)
    
    return search_items

def lambda_handler(event, context):
    print("Event - ", event)
    
    client = boto3.client('lex-runtime')
    
    dummy_string = "show me pictures of amazons"
    
    dummy_string = event['queryStringParameters']['query']
    print(dummy_string)
    
    # 'queryStringParameters': {'query': 'red'}
    response = client.post_text(
        botName='PhotoSearch',
        botAlias='photo_lex',
        userId='User1',
        # inputText=event['queryStringParameters']['query']
        inputText = dummy_string
    )
    
    print(response)
    
    search_query = get_search_query(response)
    response_es = search_elastic_search(search_query)
    
    print(response_es)
    
    # prepare response
    response = {}
    response["results"] = []
    for result in response_es['hits']['hits']:
        response_object = {}
        s3_url = 'https://photos-bucket-assignment2.s3.amazonaws.com/' + result["_source"]["objectKey"]
        response_object["url"] = s3_url
        response_object["labels"] = result["_source"]["labels"]
        response["results"].append(response_object)

    response_to_return = {
        'statusCode': 200,
        'headers': {
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        },
        'body': json.dumps(response)
    }
    
    print(response_to_return)
    return response_to_return

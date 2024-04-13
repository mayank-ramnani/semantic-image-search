import json
import boto3
from opensearchpy import OpenSearch, Urllib3AWSV4SignerAuth, Urllib3HttpConnection
import os
import logging
from os import environ
from urllib.parse import urlparse
from boto3 import Session

logger = logging.getLogger()
logger.setLevel(logging.INFO)

region = 'us-east-1'
lex = boto3.client('lexv2-runtime', region_name=region)
def lambda_handler(event, context):
    print(event)
    query = event['queryStringParameters']['q']
    
    keywords = get_keywords(query)
    
    if len(keywords) != 0:
        photo_urls = get_photo_url(keywords)
    
    if not photo_urls:
        return{
            'statusCode':200,
            "headers": {"Access-Control-Allow-Origin":"*"},
            'body': json.dumps('No Results found')
        }
    else:    
        return{
            'statusCode': 200,
            'headers': {"Access-Control-Allow-Origin":"*"},
            'body': json.dumps({
                'photoUrls':photo_urls,
                'userQuery':query,
                'keywords': keywords,
            }),
            'isBase64Encoded': False
        }

def get_keywords(query):
    response = lex.recognize_text(
        botId="2XHVE59PH5",              
        botAliasId="NT1DRKCSMS",
        localeId="en_US",
        sessionId="1234",
        text=query
    )
    
    keywords = []
    
    if 'interpretations' in response and response['interpretations']:
        for interpretation in response['interpretations']:
            if 'intent' in interpretation and 'slots' in interpretation['intent']:
                slots = interpretation['intent']['slots']
                for slot_key, slot_value in slots.items():
                    if slot_value and 'value' in slot_value and 'resolvedValues' in slot_value['value']:
                        keywords.extend(slot_value['value']['resolvedValues'])
    
    if keywords:
        print("keywords:", keywords)
    else:
        print("No keywords match'{}'".format(query))

    return keywords
    

def get_photo_url(keywords):
    credentials = boto3.Session().get_credentials()
    
    url = urlparse("https://search-photos-gns7kpxxzkxowu6t3566luo3ta.us-east-1.es.amazonaws.com")
    region = environ.get("AWS_REGION", "us-east-1")
    service = environ.get("SERVICE", "es")

    credentials = Session().get_credentials()
    print("cred: ",credentials)

    auth = Urllib3AWSV4SignerAuth(credentials, region, service)

    es = OpenSearch(
        hosts=[{"host": url.netloc, "port": url.port or 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=Urllib3HttpConnection,
        timeout=30,
    )
    
    result = []
    for keyword in keywords:
        if (keyword is not None) and keyword != '':
            searchData = es.search({"query": {"match": {"labels": keyword}}})
            result.append(searchData)
    print(result)
    
    s3_client = boto3.client(
        's3',
        region_name=region,
        aws_access_key_id=os.environ['ACCESS_KEY'],
        aws_secret_access_key=os.environ['SECRET_ACCESS_KEY'],
    )
    
    output = []
    for r in result:
        if 'hits' in r:
            for val in r['hits']['hits']:
                key = val['_source']['objectKey']
                if key not in output:
                    url = s3_client.generate_presigned_url(
                        ClientMethod='get_object',
                        Params={'Bucket': 'photo-storage-bucket-b2', 'Key': key, },
                        ExpiresIn=600000,
                    )
                    output.append(url)

    return output
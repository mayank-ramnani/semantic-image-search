import boto3
import logging
from botocore.exceptions import ClientError
import json
import base64
from urllib.parse import urlparse
from os import environ
from boto3 import Session
from opensearchpy import OpenSearch, Urllib3AWSV4SignerAuth, Urllib3HttpConnection

# Instantiate logger
logger = logging.getLogger(__name__)

# connect to the Rekognition client
rekognition = boto3.client('rekognition')

def lambda_handler(event, context):
    print(event)
    # print(context)
    try:
        for record in event["Records"]:
            # print(record["object"])
            bucket = record["s3"]["bucket"]["name"]
            image_key = record["s3"]["object"]["key"]
            # print(bucket)
            # print(image_key)
            image = None
            if 's3' in record:
                s3 = boto3.client("s3")
                obj = s3.get_object(Bucket=bucket,
                                    Key=image_key)
                
                
                image = obj['Body'].read()
                print("got image")
                # print(image)
                
                response = rekognition.detect_labels(Image={'Bytes': image})
                labels = [label['Name'] for label in response['Labels']]
                print("Labels found:")
                print(labels)

                # add custom labels from metadata
                head = s3.head_object(Bucket=bucket,
                                    Key=image_key)
                print(head)
                customLabels = head["Metadata"]["customlabels"]
                customLabelsArray = customLabels.split(",")
                print("customLabels", customLabelsArray)
                labels.extend(customLabelsArray)
                print("newlabels", labels)
                json_obj = {
                    "objectKey": image_key,
                    "bucket": bucket,
                    "createdTimestamp": record["eventTime"],
                    "labels": [labels]
                }
                print(json_obj)
                lambda_response = {
                    "statusCode": 200,
                    "body": json.dumps(response)
                }
                
                url = urlparse("https://search-photos-gns7kpxxzkxowu6t3566luo3ta.us-east-1.es.amazonaws.com")
                region = environ.get("AWS_REGION", "us-east-1")
                service = environ.get("SERVICE", "es")

                credentials = Session().get_credentials()
                print(credentials)
                auth = Urllib3AWSV4SignerAuth(credentials, region, service)
                print(auth)

                client = OpenSearch(
                    hosts=[{"host": url.netloc, "port": url.port or 443}],
                    http_auth=auth,
                    use_ssl=True,
                    verify_certs=True,
                    connection_class=Urllib3HttpConnection,
                    timeout=30,
                )

                # TODO: remove when OpenSearch Serverless adds support for /
                if service == "es":
                    info = client.info()
                    # print(f"{info['version']['distribution']}: {info['version']['number']}")

                # create an index
                index = "photos"
                # only need to create it the first time
                # client.indices.create(index=index)
                # client.indices.delete(index=index)
                client.index(index=index, body=json_obj)
                # client.index(index=index, body=json_obj, id=identifier)

                
    except ClientError as client_err:
       error_message = "Couldn't analyze image: " + client_err.response['Error']['Message']

       lambda_response = {
           'statusCode': 400,
           'body': {
               "Error": client_err.response['Error']['Code'],
               "ErrorMessage": error_message
           }
       }
       logger.error("Error function %s: %s",
                    context.invoked_function_arn, error_message)

    except ValueError as val_error:
        lambda_response = {
            'statusCode': 400,
            'body': {
                "Error": "ValueError",
                "ErrorMessage": format(val_error)
            }
        }
        logger.error("Error function %s: %s",
                     context.invoked_function_arn, format(val_error))
    return lambda_response
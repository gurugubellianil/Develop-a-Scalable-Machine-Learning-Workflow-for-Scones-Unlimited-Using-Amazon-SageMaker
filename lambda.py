""" 
The first lambda function is responsible for data generation.
SerializeImageData: A lambda function that copies an object from S3, base64 encodes it, and 
then return it (serialized data) to the step function as `image_data` in an event.
"""

import json
import boto3
import base64
# import botocore

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """A function to serialize target data from S3"""
    
    # Get the s3 address from the Step Function event input
    key =event["s3_key"] ## TODO: fill in
    bucket =event["s3_bucket"] ## TODO: fill in
    
    # Download the data from s3 to /tmp/image.png
    ## TODO: fill in
    boto3.resource('s3').Bucket(bucket).download_file(key, "/tmp/image.png")
    
    # We read the data from a file
    with open("/tmp/image.png", "rb") as f:
        image_data = base64.b64encode(f.read())

    # Pass the data back to the Step Function
    print("Event:", event.keys())
    return {
        'statusCode': 200,
        'body': {
            "image_data": image_data,
            "s3_bucket": bucket,
            "s3_key": key,
            "inferences": []
        }
    }


""" 
The second one is responsible for image classification.
It takes the image output from the lambda 1 function(SerializeImageData), decodes it, and then pass inferences back to the the Step Function.
"""

import os
import io
import boto3
import json
import base64
# import sagemaker
# from sagemaker.serializers import IdentitySerializer


# setting the  environment variables
ENDPOINT_NAME = "image-classification-2024-09-02-17-49-24-343"
# # We will be using the AWS's lightweight runtime solution to invoke an endpoint.
runtime= boto3.client('runtime.sagemaker')

def lambda_handler(event, context):

    # # Decode the image data
    image = base64.b64decode(event["body"]['image_data'])
    
    # Make a prediction:
    predictor = runtime.invoke_endpoint(EndpointName=ENDPOINT_NAME,
                                    #   ContentType='image/png',
                                    ContentType='application/x-image',
                                      Body=image)
    
    # We return the data back to the Step Function    
    event["inferences"] = json.loads(predictor['Body'].read().decode('utf-8'))
    return {
        'statusCode': 200,
        # 'body': json.dumps(event)
        "body": {
            "image_data": event["body"]['image_data'],
            "s3_bucket": event["body"]['s3_bucket'],
            "s3_key": event["body"]['s3_key'],
            "inferences": event['inferences'],
       }
    }


""" 
The third function is responsible for filtering out low-confidence inferences.
It takes the inferences from the Lambda 2 function output and filters low-confidence inferences above a certain threshold indicating success"
"""
import json
THRESHOLD = .8
def lambda_handler(event, context):
    # Get the inferences from the event
    inferences = event["body"]["inferences"]
    
    # Check if any values in any inferences are above THRESHOLD
    meets_threshold = (max(inferences) > THRESHOLD)
    
    if meets_threshold:
        pass
    else:
        raise("THRESHOLD_CONFIDENCE_NOT_MET")

    return {
        'statusCode': 200,
        'body': json.dumps(event)
    }
import logging
import subprocess
import fcsparser
import boto3
import json
import requests
import time

SIGNED_URL_EXPIRATION = 300     # The number of seconds that the Signed URL is valid
DYNAMODB_TABLE_NAME = "TechnicalMetadata"
DYNAMO = boto3.resource("dynamodb")
TABLE = DYNAMO.Table(DYNAMODB_TABLE_NAME)

logger = logging.getLogger('boto3')
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """

    :param event:
    :param context:
    """
    # Loop through records provided by S3 Event trigger
    for s3_record in event['Records']:
        logger.info("Working on new s3_record...")
        # Extract the Key and Bucket names for the asset uploaded to S3
        key = s3_record['s3']['object']['key']
        bucket = s3_record['s3']['bucket']['name']
        logger.info("Bucket: {} \t Key: {}".format(bucket, key))
        record = extract_record(bucket, key)
        save_record(key, record['fcs_metadata'], record['fcs_channels'], record['s3_metadata'])
        announce_record(bucket, key, record['fcs_metadata'], record['s3_metadata'])

def announce_record(bucket, key, fcs_metadata, s3_metadata):
    pretext = "{trial} {assay} {tubetype} {fcsfile} uploaded as {key}".format(trial=s3_metadata['trial'],assay=s3_metadata['assay'],tubetype=s3_metadata['tubetype'],fcsfile=s3_metadata['qqfilename'],key=key)

    s3 = boto3.client('s3')
    signed_url = s3.generate_presigned_url(
        'get_object', 
        Params = { 
        'Bucket': bucket, 
        'Key': key,
        'ResponseContentDisposition': 'attachment; filename={}'.format(s3_metadata['qqfilename'])
        }, 
        ExpiresIn = SIGNED_URL_EXPIRATION, )

    
    slack_data = """{{
    "attachments": [
        {{
            "fallback": "{pretext}",
            "color": "#36a64f",
            "pretext": "New upload",
            "title": "{title}",
            "title_link": "{url}",
            "text": "This url will expire in 300 seconds",
            "fields": [
                {{
                    "title": "Trial",
                    "value": "{trial}",
                    "short": true
                }},
                {{
                    "title": "Assay",
                    "value": "{assay}",
                    "short": true
                }},
                {{
                    "title": "Tube type",
                    "value": "{tubetype}",
                    "short": true
                }}
            ],
            "footer_icon": "https://s3.amazonaws.com/cytovas-public/favicon-36.png",
            "footer": "FCS Uploader",
            "ts": {now}
        }}
    ]
}}
""".format(pretext=pretext,url=signed_url,title=s3_metadata['qqfilename'],trial=s3_metadata['trial'],assay=s3_metadata['assay'],tubetype=s3_metadata['tubetype'],now=time.time())

    webhook_url = 'https://hooks.slack.com/services/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'
    response = requests.post(
        webhook_url, data=slack_data,
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code != 200:
        raise ValueError(
           'Request to slack returned an error %s, the response is:\n%s'
            % (response.status_code, response.text)
        )

def extract_record(bucket, key):
    s3 = boto3.resource('s3')
    s3_object = s3.Object(bucket, key)

    s3.Bucket(bucket).download_file(key, '/tmp/'+key)
    
    logger.info("i hope fcsparser can handle {0}".format('/tmp/'+key))
    
    fcs_metadata = fcsparser.parse('/tmp/'+key, reformat_meta=True, meta_data_only=True)
    
    #for some reasons this is in bytes
    fcs_metadata['__header__']['FCS format'] = fcs_metadata['__header__']['FCS format'].decode('ascii')
    
    #dynamo doesn't like tuples
    fcs_metadata['_channel_names_'] = list(fcs_metadata['_channel_names_'])
    
    #pandas dataframe
    channels = fcs_metadata.pop('_channels_', None)
    
    #this gets serialized as json so it can be stored in dynamodb
    fcs_channels=channels.to_json()
    
    return({'fcs_metadata':dict(fcs_metadata),'fcs_channels':fcs_channels,'s3_metadata':s3_object.metadata})

def save_record(key, fcs_metadata, fcs_channels, s3_metadata):
    """
    Save record to DynamoDB

    :param key:         S3 Key Name
    :param xml_output:  Technical Metadata
    :return:
    """
    logger.info("Saving record to DynamoDB...")
    TABLE.put_item(
       Item={
            'keyName': key,
            'fcs_metadata': fcs_metadata,
            'fcs_channels': fcs_channels,
            's3_metadata': s3_metadata
        }
    )
    logger.info("Saved record to DynamoDB")


def get_signed_url(expires_in, bucket, obj):
    """
    Generate a signed URL
    :param expires_in:  URL Expiration time in seconds
    :param bucket:
    :param obj:         S3 Key name
    :return:            Signed URL
    """
    s3_cli = boto3.client("s3")
    presigned_url = s3_cli.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': obj},
                                                  ExpiresIn=expires_in)
    return presigned_url

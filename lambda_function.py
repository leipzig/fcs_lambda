import logging
import subprocess
import fcsparser
import boto3

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
        # Generate a signed URL for the uploaded asset
        #signed_url = get_signed_url(SIGNED_URL_EXPIRATION, bucket, key)
        #logger.info("Signed URL: {}".format(signed_url))
        
        #response = s3.get_object(Bucket=bucket, Key=key)
        #data = response['Body'].read().decode('utf-8')
        
        s3 = boto3.resource('s3')
        s3.Bucket(bucket).download_file(key, '/tmp/'+key)
        
        meta, data = fcsparser.parse(path, reformat_meta=True, meta_data_only=True)
        
        #for some reasons this is in bytes
        meta['__header__']['FCS format'] = meta['__header__']['FCS format'].decode('ascii')
        
        #pandas dataframe
        channels = meta.pop('_channels_', None)
        
        with open('meta.txt', 'w') as f:
          json.dump(meta, f, ensure_ascii=False)
        
        channels.to_csv('channels.txt',sep="\t")
        save_record(key, xml_output)

def save_record(key, xml_output):
    """
    Save record to DynamoDB

    :param key:         S3 Key Name
    :param xml_output:  Technical Metadata in XML Format
    :return:
    """
    logger.info("Saving record to DynamoDB...")
    TABLE.put_item(
       Item={
            'keyName': key,
            'technicalMetadata': xml_output
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

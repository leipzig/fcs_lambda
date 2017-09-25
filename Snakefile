
rule lambda:
    input: "lambda_function.py"
    output: "fcs_lambda/lambda.zip"
    shell:
        """
        cp lambda_function.py fcs_lambda/
        cd fcs_lambda
        zip -r -9 -q lambda.zip *
        """

rule upload:
    input: "fcs_lambda/lambda.zip"
    shell:
        """
        aws lambda delete-function --function-name LambdaFCS
        aws lambda create-function     --function-name LambdaFCS     --runtime python3.6     --role arn:aws:iam::205853417430:role/LambdaMediaInfoExecutionRole     --handler lambda_function.lambda_handler     --description "Lambda FCS Function"     --timeout 60     --memory-size 128     --zip-file fileb://fcs_lambda/lambda.zip
        aws lambda add-permission     --function-name LambdaFCS     --statement-id Id-1     --action "lambda:InvokeFunction"     --principal s3.amazonaws.com     --source-arn arn:aws:s3:::cytovas-instrument-files     --source-account 205853417430
        aws s3api put-bucket-notification     --bucket cytovas-instrument-files     --notification-configuration file://notification.json
        """
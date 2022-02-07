from random import randint


def lambda_handler(event, context):
    # {"url":"https://ca.indeed.com/jobs?q=data+analyst&sort=date&limit=50"}
    
    # TODO: download the job posting and upload it to S3

    url = event['url']
    
    result = {
        "s3_key": url
    }
    return result

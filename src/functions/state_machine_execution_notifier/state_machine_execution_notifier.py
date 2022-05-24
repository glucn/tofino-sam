import logging
import os

from aws import SNS
from config import STATE_MACHINE_EXECUTION_NOTIFICATION_TOPIC


logging.getLogger().setLevel(logging.INFO)

_NOTIFICATION_SNS_TOPIC_ARN = os.environ[STATE_MACHINE_EXECUTION_NOTIFICATION_TOPIC]

def lambda_handler(event, context):
    # Input: {"status": "FAILED", "region": "us-west-2", "executionArn": "arn:aws:states:us-west-2:xxxxxxxx:execution:IndeedJobStateMachine-FcPDQL2GxuEV:37f601e5-1dc8-4b29-82e0-3b35059c7f31"}

    status = event['status']
    region = event['region']
    executionArn = event['executionArn']

    subject = f"[Action Required] Tofino statemachine execution got {status} status"

    message = f"https://{region}.console.aws.amazon.com/states/home?region={region}#/v2/executions/details/{executionArn}" # Enrich the message later

    SNS.publish(
        target_arn=_NOTIFICATION_SNS_TOPIC_ARN,
        message=message,
        subject=subject
        )

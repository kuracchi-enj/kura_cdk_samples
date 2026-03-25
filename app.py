#!/usr/bin/env python3
import os
from pathlib import Path

import aws_cdk as cdk
from dotenv import load_dotenv

from stacks.cdk_api_lambda_stack import CdkApiLambdaStack
from stacks.cdk_durable_lambda_stack import CdkDurableLambdaStack
from stacks.cdk_ec2_stack import CdkEc2Stack
from stacks.cdk_elastic_beanstalk_stack import CdkElasticBeanstalkStack
from stacks.cdk_lambda_stack import CdkLambdaStack
from stacks.cdk_rds_stack import CdkRdsStack


load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

app = cdk.App()

CdkEc2Stack(
    app,
    "CdkEc2Stack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
)

CdkLambdaStack(
    app,
    "CdkLambdaStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
)

CdkRdsStack(
    app,
    "CdkRdsStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
)

CdkApiLambdaStack(
    app,
    "CdkApiLambdaStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
)

CdkElasticBeanstalkStack(
    app,
    "CdkElasticBeanstalkStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
)

# Durable Functions は現時点では利用可能リージョンが限られる (us-east-2 など)
# デプロイ前に対象リージョンで利用可能か確認すること
CdkDurableLambdaStack(
    app,
    "CdkDurableLambdaStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
)

app.synth()


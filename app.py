#!/usr/bin/env python3
import os
from pathlib import Path

import aws_cdk as cdk
from dotenv import load_dotenv

from cdk_ec2_stack import CdkEc2Stack
from cdk_lambda_stack import CdkLambdaStack
from cdk_rds_stack import CdkRdsStack


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

app.synth()

from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_apigateway as apigw,
    aws_lambda as lambda_,
)
from constructs import Construct


class CdkApiLambdaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        fn = lambda_.Function(
            self,
            "HelloFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="handler.handler",
            code=lambda_.Code.from_asset("lambda"),
            timeout=Duration.seconds(30),
        )

        api = apigw.RestApi(
            self,
            "HelloApi",
            rest_api_name="hello-api",
            description="API Gateway backed by Lambda",
        )

        api.root.add_method("GET", apigw.LambdaIntegration(fn))

        CfnOutput(self, "ApiUrl", value=api.url)

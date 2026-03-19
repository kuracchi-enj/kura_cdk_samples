from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_lambda as lambda_,
)
from constructs import Construct


class CdkLambdaStack(Stack):
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

        fn_url = fn.add_function_url(
            auth_type=lambda_.FunctionUrlAuthType.NONE,
        )

        CfnOutput(self, "FunctionUrl", value=fn_url.url)

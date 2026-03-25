from aws_cdk import (
    CfnOutput,
    RemovalPolicy,
    Stack,
    aws_ec2 as ec2,
    aws_rds as rds,
)
from constructs import Construct


class CdkRdsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc.from_lookup(self, "DefaultVpc", is_default=True)

        db = rds.DatabaseInstance(
            self,
            "PostgresInstance",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_17
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
            credentials=rds.Credentials.from_generated_secret("postgres"),
            database_name="appdb",
            allocated_storage=20,
            deletion_protection=False,
            removal_policy=RemovalPolicy.DESTROY,
        )

        CfnOutput(self, "DbEndpoint", value=db.db_instance_endpoint_address)
        CfnOutput(self, "DbPort", value=db.db_instance_endpoint_port)
        CfnOutput(
            self,
            "DbSecretArn",
            value=db.secret.secret_arn,
        )

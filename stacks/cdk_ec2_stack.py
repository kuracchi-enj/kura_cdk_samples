from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class CdkEc2Stack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Reuse the default VPC in the target account/region instead of creating a new one.
        vpc = ec2.Vpc.from_lookup(self, "DefaultVpc", is_default=True)

        ec2.Instance(
            self,
            "Instance",
            vpc=vpc,
            instance_type=ec2.InstanceType("t3.micro"),
            machine_image=ec2.MachineImage.latest_amazon_linux2023(),
            ssm_session_permissions=True,
        )

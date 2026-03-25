from aws_cdk import (
    CfnOutput,
    Fn,
    RemovalPolicy,
    Stack,
    aws_ec2 as ec2,
    aws_elasticbeanstalk as eb,
    aws_iam as iam,
    aws_rds as rds,
)
from constructs import Construct


class CdkElasticBeanstalkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc.from_lookup(self, "DefaultVpc", is_default=True)

        # Security group for Elastic Beanstalk EC2 instances
        eb_sg = ec2.SecurityGroup(
            self,
            "EbSecurityGroup",
            vpc=vpc,
            description="Security group for Elastic Beanstalk instances",
        )

        # Security group for RDS — allows inbound from EB instances only
        db_sg = ec2.SecurityGroup(
            self,
            "DbSecurityGroup",
            vpc=vpc,
            description="Security group for RDS PostgreSQL",
        )
        db_sg.add_ingress_rule(
            peer=eb_sg,
            connection=ec2.Port.tcp(5432),
            description="Allow Elastic Beanstalk instances to connect to PostgreSQL",
        )

        # RDS PostgreSQL
        # 以下のリソースが暗黙的に自動作成される:
        #   - DB サブネットグループ (VPC 内配置に必要)
        #   - DB パラメータグループ (デフォルト設定が自動適用)
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
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_groups=[db_sg],
            # Secrets Manager にシークレット（ユーザー名・パスワード等）を自動生成し、RDS に設定する
            credentials=rds.Credentials.from_generated_secret("postgres"),
            database_name="app_production",
            allocated_storage=20,
            deletion_protection=False,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # IAM Role for EC2 instances in the EB environment
        # grant_read() 呼び出し時に Secrets Manager への GetSecretValue 権限を持つ
        # インラインポリシーが自動でロールにアタッチされる
        eb_role = iam.Role(
            self,
            "EbInstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AWSElasticBeanstalkWebTier"
                ),
            ],
        )
        # Allow EB instances to read the DB credentials from Secrets Manager
        db.secret.grant_read(eb_role)

        instance_profile = iam.CfnInstanceProfile(
            self,
            "EbInstanceProfile",
            roles=[eb_role.role_name],
        )

        # Elastic Beanstalk Application
        application = eb.CfnApplication(
            self,
            "RailsApp",
            application_name="rails-app",
            description="Ruby on Rails application",
        )

        # Comma-separated public subnet IDs for VPC settings
        public_subnet_ids = Fn.join(
            ",", [subnet.subnet_id for subnet in vpc.public_subnets]
        )

        # Elastic Beanstalk Environment
        # 以下のリソースが暗黙的に自動作成される:
        #   - Auto Scaling Group / Application Load Balancer (LoadBalanced タイプのため)
        #   - Launch Template (EC2 起動設定)
        #   - EB サービスロール (aws-elasticbeanstalk-service-role)
        #   - CloudWatch ロググループ (ログストリーミング用)
        #   - S3 バケット (デプロイアーティファクト保存用、リージョンごとに共有)
        # To find the latest solution stack name, run:
        #   aws elasticbeanstalk list-available-solution-stacks \
        #     --query "SolutionStacks[?contains(@, 'Ruby')]"
        environment = eb.CfnEnvironment(
            self,
            "RailsEnv",
            application_name=application.ref,
            environment_name="rails-env",
            solution_stack_name="64bit Amazon Linux 2023 v4.11.0 running Ruby 3.3",
            option_settings=[
                # VPC
                eb.CfnEnvironment.OptionSettingProperty(
                    namespace="aws:ec2:vpc",
                    option_name="VPCId",
                    value=vpc.vpc_id,
                ),
                eb.CfnEnvironment.OptionSettingProperty(
                    namespace="aws:ec2:vpc",
                    option_name="Subnets",
                    value=public_subnet_ids,
                ),
                eb.CfnEnvironment.OptionSettingProperty(
                    namespace="aws:ec2:vpc",
                    option_name="ELBSubnets",
                    value=public_subnet_ids,
                ),
                # Instance type
                eb.CfnEnvironment.OptionSettingProperty(
                    namespace="aws:ec2:instances",
                    option_name="InstanceTypes",
                    value="t3.micro",
                ),
                # IAM instance profile
                eb.CfnEnvironment.OptionSettingProperty(
                    namespace="aws:autoscaling:launchconfiguration",
                    option_name="IamInstanceProfile",
                    value=instance_profile.ref,
                ),
                # Attach the EB security group to EC2 instances
                eb.CfnEnvironment.OptionSettingProperty(
                    namespace="aws:autoscaling:launchconfiguration",
                    option_name="SecurityGroups",
                    value=eb_sg.security_group_id,
                ),
                # Load-balanced environment
                eb.CfnEnvironment.OptionSettingProperty(
                    namespace="aws:elasticbeanstalk:environment",
                    option_name="EnvironmentType",
                    value="LoadBalanced",
                ),
                # Rails / DB environment variables
                eb.CfnEnvironment.OptionSettingProperty(
                    namespace="aws:elasticbeanstalk:application:environment",
                    option_name="RAILS_ENV",
                    value="production",
                ),
                eb.CfnEnvironment.OptionSettingProperty(
                    namespace="aws:elasticbeanstalk:application:environment",
                    option_name="DATABASE_HOST",
                    value=db.db_instance_endpoint_address,
                ),
                eb.CfnEnvironment.OptionSettingProperty(
                    namespace="aws:elasticbeanstalk:application:environment",
                    option_name="DATABASE_PORT",
                    value=db.db_instance_endpoint_port,
                ),
                eb.CfnEnvironment.OptionSettingProperty(
                    namespace="aws:elasticbeanstalk:application:environment",
                    option_name="DATABASE_NAME",
                    value="app_production",
                ),
                # Pass the Secrets Manager ARN; the Rails app reads credentials from it
                eb.CfnEnvironment.OptionSettingProperty(
                    namespace="aws:elasticbeanstalk:application:environment",
                    option_name="DATABASE_SECRET_ARN",
                    value=db.secret.secret_arn,
                ),
            ],
        )
        environment.add_dependency(application)

        CfnOutput(self, "EbEndpointUrl", value=environment.attr_endpoint_url)
        CfnOutput(self, "DbEndpoint", value=db.db_instance_endpoint_address)
        CfnOutput(self, "DbSecretArn", value=db.secret.secret_arn)

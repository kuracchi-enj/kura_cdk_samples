from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_iam as iam,
    aws_lambda as lambda_,
)
from constructs import Construct


class CdkDurableLambdaStack(Stack):
    """
    Lambda Durable Functions を有効にしたスタック。

    Durable Functions は re:Invent 2025 で発表された機能で、
    最大 1 年間実行できるチェックポイント/リプレイ機能付きの Lambda 関数を構築できる。

    主な特徴:
      - step(): チェックポイント + 自動リトライ付きで処理を実行
      - wait(): 一時停止中はコンピュートチャージなし
      - 最大 1 年間の実行（ExecutionTimeout で指定）

    制約:
      - 現時点では利用可能リージョンが限られる (us-east-2 など)
      - 既存の Lambda 関数に後から有効化することはできない（新規作成時のみ）
      - 呼び出しにはバージョン/エイリアスの修飾 ARN が必要
      - ランタイムは Python 3.13/3.14 または Node.js 22/24 が必要
      - CDK v2.232.0 以上が必要

    必要な CDK バージョン: aws-cdk-lib >= 2.232.0
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        fn = lambda_.Function(
            self,
            "DurableHelloFunction",
            function_name="durable-hello",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="handler.handler",
            # lambda_durable/ 以下に SDK を含めてデプロイする
            # pip install -r lambda_durable/requirements.txt -t lambda_durable/ を事前に実行すること
            code=lambda_.Code.from_asset("lambda_durable"),
            timeout=Duration.seconds(30),
            # Durable Functions を有効化する設定
            # execution_timeout: ワークフロー全体の最大実行時間（最大 1 年）
            # retention_period: 実行履歴を保持する日数（1〜90 日）
            durable_config=lambda_.DurableConfig(
                execution_timeout=Duration.hours(1),
                retention_period=Duration.days(7),
            ),
        )

        # Durable Functions のチェックポイント操作に必要なマネージドポリシーを付与する
        # 含まれる権限: lambda:CheckpointDurableExecutions, lambda:GetDurableExecutionState
        fn.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AWSLambdaBasicDurableExecutionRolePolicy"
            )
        )

        # Durable Functions の呼び出しには修飾 ARN（バージョンまたはエイリアス）が必要
        version = fn.current_version

        alias = lambda_.Alias(
            self,
            "ProdAlias",
            alias_name="prod",
            version=version,
        )

        # 呼び出し時はこの ARN を使うこと
        CfnOutput(
            self,
            "FunctionAliasArn",
            value=alias.function_arn,
            description="Durable Function の呼び出しにはこの ARN を使用すること",
        )

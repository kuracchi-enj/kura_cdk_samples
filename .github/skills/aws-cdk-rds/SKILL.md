---
name: aws-cdk-rds
description: AWS CDK (Python) でRDS PostgreSQLインスタンスをデプロイするスタックを生成するスキル。デフォルトVPC再利用・Secrets Manager認証情報管理・db.t3.micro構成。
---

# AWS CDK RDS Stack Skill

AWS CDK (Python) でRDS PostgreSQLインスタンスをデプロイするための `CdkRdsStack` を生成します。
認証情報はSecrets Managerで自動生成・管理されます。

## When to use

- CDKプロジェクトにRDS PostgreSQLインスタンスを追加したいとき
- データベースのパスワードをSecrets Managerで安全に管理したいとき
- 開発・検証用の小規模なRDS環境を素早く構築したいとき

## Instructions

1. **`cdk_rds_stack.py`** を以下の内容で作成する:
```python
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
```

2. **`app.py`** に以下を追加する:
```python
from cdk_rds_stack import CdkRdsStack

CdkRdsStack(
    app,
    "CdkRdsStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
)
```

3. `cdk synth CdkRdsStack` でテンプレート生成を確認する。

4. デプロイするときは `cdk deploy CdkRdsStack` を実行する。デプロイ完了後、Outputsに以下が表示される:
   - `DbEndpoint` — 接続エンドポイント
   - `DbPort` — ポート番号（デフォルト: 5432）
   - `DbSecretArn` — Secrets ManagerのARN

5. パスワードを取得するときは以下のコマンドを使う:
```bash
aws secretsmanager get-secret-value --secret-id <DbSecretArn> --query SecretString --output text
```

## Key Design Decisions

- **PostgreSQL 17**: `PostgresEngineVersion.VER_17` を使用。バージョンを変更する場合は `VER_16` などに修正する。
- **db.t3.micro**: 開発・検証用の最小インスタンス。本番環境では `BURSTABLE3` + `SMALL` 以上を推奨。
- **Secrets Manager自動生成**: `Credentials.from_generated_secret("postgres")` で30文字のランダムパスワードを自動生成しSecrets Managerに保存する。アプリからはARNを使って認証情報を取得できる。
- **デフォルトVPC・パブリックサブネット**: 開発用に `SubnetType.PUBLIC` を使用。本番環境では `PRIVATE_WITH_EGRESS` または `PRIVATE_ISOLATED` を推奨。
- **RemovalPolicy.DESTROY**: スタック削除時にDBインスタンスも削除される。本番環境では `RETAIN` に変更すること。
- **deletion_protection=False**: 開発用に削除保護を無効化。本番環境では `True` に変更すること。
- **CfnOutput**: エンドポイント・ポート・SecretARNをOutputsとして出力し、デプロイ後すぐに接続情報を確認できるようにする。

---
name: aws-cdk-lambda
description: AWS CDK (Python) でLambda関数をFunction URL付きでデプロイするスタックを生成するスキル。API Gatewayなし・Python 3.13・認証なしURLエンドポイント構成。
---

# AWS CDK Lambda Stack Skill

AWS CDK (Python) でLambda関数をデプロイするための `CdkLambdaStack` を生成します。
API Gatewayを使わず Lambda Function URL でHTTPエンドポイントを公開します。

## When to use

- CDKプロジェクトにLambda関数を追加したいとき
- API GatewayなしでHTTPエンドポイントを公開したいとき
- Lambda Function URLを使いたいとき

## Instructions

1. **`lambda/handler.py`** を作成する:
```python
import json


def handler(event, context):
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"message": "Hello from Lambda!"}),
    }
```

2. **`cdk_lambda_stack.py`** を以下の内容で作成する:
```python
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
```

3. **`app.py`** に以下を追加する:
```python
from cdk_lambda_stack import CdkLambdaStack

CdkLambdaStack(
    app,
    "CdkLambdaStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
)
```

4. `cdk synth CdkLambdaStack` でテンプレート生成を確認する。

5. デプロイするときは `cdk deploy CdkLambdaStack` を実行する。デプロイ完了後、Outputsに Function URL が表示される。

6. 動作確認:
```bash
curl <FunctionUrl>
# => {"message": "Hello from Lambda!"}
```

## Key Design Decisions

- **Lambda Function URL**: `add_function_url(auth_type=NONE)` でAPI Gatewayなしの公開HTTPエンドポイントを作成する。認証が必要な場合は `AWS_IAM` に変更する。
- **Python 3.13**: `Runtime.PYTHON_3_13` を使用。ランタイムを変更する場合は `handler.py` の互換性も確認すること。
- **コードパス**: `Code.from_asset("lambda")` で `lambda/` ディレクトリをZIPしてデプロイする。
- **CfnOutput**: Function URLをスタックのOutputとして出力し、デプロイ後すぐにURLを確認できるようにする。
- **タイムアウト**: デフォルト30秒。処理内容に応じて調整すること（最大15分）。

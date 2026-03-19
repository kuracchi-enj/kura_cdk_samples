---
name: aws-cdk-ec2
description: AWS CDK (Python) でEC2インスタンスをデプロイするスタックを生成するスキル。デフォルトVPC再利用・SSMセッション許可・Amazon Linux 2023構成。
---

# AWS CDK EC2 Stack Skill

AWS CDK (Python) でEC2インスタンスをデプロイするための `CdkEc2Stack` を生成します。
新規VPCを作らずデフォルトVPCを再利用し、コストを最小化する構成です。

## When to use

- CDKプロジェクトにEC2インスタンスを追加したいとき
- デフォルトVPCにt3.microインスタンスを立てたいとき
- SSH不要でSSM Session Managerからアクセスしたいとき

## Instructions

1. **`cdk_ec2_stack.py`** を以下の内容で作成する:
```python
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
```

2. **`app.py`** に以下を追加する:
```python
from cdk_ec2_stack import CdkEc2Stack

CdkEc2Stack(
    app,
    "CdkEc2Stack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
)
```

3. `cdk synth CdkEc2Stack` でテンプレート生成を確認する。

4. デプロイするときは `cdk deploy CdkEc2Stack` を実行する。

## Key Design Decisions

- **デフォルトVPC再利用**: `ec2.Vpc.from_lookup(is_default=True)` でアカウントのデフォルトVPCを参照し、新規VPC作成コストを省く。
- **SSMセッション許可**: `ssm_session_permissions=True` によりSSH不要でインスタンスへ接続可能。キーペア管理が不要になる。
- **Amazon Linux 2023**: `MachineImage.latest_amazon_linux2023()` で常に最新のAL2023 AMIを使用する。
- **インスタンスタイプ**: デフォルトは `t3.micro`。変更する場合は `instance_type` を修正する。

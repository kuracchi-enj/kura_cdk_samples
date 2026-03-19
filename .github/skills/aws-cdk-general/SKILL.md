---
name: aws-cdk-general
description: AWS CDK (Python) プロジェクトの共通セットアップスキル。app.py・requirements.txt・.env・cdk.json などプロジェクト基盤を生成する。
---

# AWS CDK General Setup Skill

AWS CDK (Python) プロジェクトの共通基盤（エントリーポイント・依存関係・環境変数管理）をセットアップします。
個別のリソーススタック（EC2・Lambda等）は別スキルで追加します。

## When to use

- 新しい AWS CDK (Python) プロジェクトをゼロから始めるとき
- `app.py` や `requirements.txt` などの共通ファイルを生成したいとき
- 環境変数（AWSアカウント・リージョン・プロファイル）を `.env` で管理したいとき

## Instructions

1. 対象ディレクトリで仮想環境を作成し、依存関係をインストールする:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. **`requirements.txt`** を以下の内容で作成する:
```
aws-cdk-lib==2.243.0
constructs>=10.0.0,<11.0.0
python-dotenv>=1.0.0,<2.0.0
```

3. **`cdk.json`** を作成する:
```json
{
  "app": ".venv/bin/python app.py"
}
```

4. **`.env.example`** を作成する:
```
# Copy to .env and fill in local values. Do not commit .env.
AWS_PROFILE=your-aws-profile
CDK_DEFAULT_ACCOUNT=123456789012
CDK_DEFAULT_REGION=ap-northeast-1
```

5. **`.gitignore`** に以下を追加する:
```
.env
.venv/
cdk.out/
__pycache__/
*.pyc
```

6. **`app.py`** をスタック構成に合わせて作成する。スタックが増えるたびにここへ追加する:
```python
#!/usr/bin/env python3
import os
from pathlib import Path

import aws_cdk as cdk
from dotenv import load_dotenv

# スタックのimportをここに追加
# from cdk_ec2_stack import CdkEc2Stack
# from cdk_lambda_stack import CdkLambdaStack


load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

app = cdk.App()

# スタックのインスタンス化をここに追加
# CdkEc2Stack(app, "CdkEc2Stack", env=cdk.Environment(...))
# CdkLambdaStack(app, "CdkLambdaStack", env=cdk.Environment(...))

app.synth()
```

7. `.env.example` を `.env` にコピーし、実際の値を設定するようユーザーに案内する。

8. `cdk synth` でテンプレート生成を確認する。

## Key Design Decisions

- **スタック分離**: 各リソース（EC2・Lambda等）を独立したスタックファイルに分け、`cdk deploy <StackName>` で個別デプロイを可能にする。
- **環境変数管理**: `python-dotenv` で `.env` から `CDK_DEFAULT_ACCOUNT` / `CDK_DEFAULT_REGION` / `AWS_PROFILE` を読み込む。`.env` は絶対にコミットしない。

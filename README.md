# kura_cdk_samples

AWS CDK (Python) を使って各種 AWS リソースをデプロイするためのサンプル集です。

スタックは用途ごとに分割されており、必要なスタックだけを個別にデプロイできます。
現在は EC2・Lambda・RDS・Lambda+API Gateway・Elastic Beanstalk を提供しており、今後も順次追加予定です。

## 提供スタック一覧

| スタック | ファイル | 作成されるリソース |
|---------|---------|-----------------|
| EC2 | `stacks/cdk_ec2_stack.py` | EC2 インスタンス (t3.micro / AL2023 / SSM) |
| Lambda | `stacks/cdk_lambda_stack.py` | Lambda 関数 + Function URL |
| RDS | `stacks/cdk_rds_stack.py` | RDS PostgreSQL 17 (db.t3.micro) + Secrets Manager |
| Lambda + API Gateway | `stacks/cdk_api_lambda_stack.py` | Lambda 関数 + API Gateway REST API |
| Elastic Beanstalk | `stacks/cdk_elastic_beanstalk_stack.py` | EB アプリ + 環境 + RDS PostgreSQL (Ruby on Rails 想定) |
| CdkDurableLambdaStack | `stacks/cdk_durable_lambda_stack.py` | Lambda Durable Functions (チェックポイント/リプレイ) |

## 設計方針

- スタックは用途ごとに独立したファイルに分割する
- 新しい VPC は作らず、既存の default VPC を再利用する
- 認証情報は Secrets Manager で管理し、コードにハードコードしない
- 環境固有の値は `.env` で管理し、Git にコミットしない

## ファイル構成

```
.
├── app.py                    # CDK アプリのエントリーポイント
├── cdk.json                  # CDK CLI 設定
├── stacks/
│   ├── __init__.py
│   ├── cdk_ec2_stack.py          # EC2 スタック
│   ├── cdk_lambda_stack.py       # Lambda スタック
│   ├── cdk_api_lambda_stack.py   # Lambda + API Gateway スタック
│   ├── cdk_rds_stack.py          # RDS スタック
│   ├── cdk_elastic_beanstalk_stack.py  # Elastic Beanstalk スタック
│   └── cdk_durable_lambda_stack.py     # Lambda Durable Functions スタック
├── lambda/
│   └── handler.py            # Lambda ハンドラー
├── lambda_durable/
│   ├── handler.py            # Durable Functions ハンドラー
│   └── requirements.txt      # Lambda 用 SDK
├── requirements.txt          # Python 依存ライブラリ
├── .env.example              # 環境変数の雛形
├── .github/
│   ├── hooks/
│   │   └── hooks.json        # Copilot CLI フック定義
│   └── skills/               # Copilot CLI スキル定義
│       ├── aws-cdk-general/
│       ├── aws-cdk-ec2/
│       ├── aws-cdk-lambda/
│       └── aws-cdk-rds/
└── .gitignore
```

## 前提条件

- Python 3 がインストールされている
- AWS CDK CLI がインストールされている (`npm install -g aws-cdk`)
- AWS CLI で認証済みである
- デプロイ先アカウント・リージョンに default VPC が存在する

確認コマンド:

```bash
python3 --version
cdk --version
aws sts get-caller-identity
```

## セットアップ

### 1. `.env` を作成する

```bash
cp .env.example .env
```

`.env` の値:

| 変数 | 説明 |
|-----|------|
| `AWS_PROFILE` | 使用する AWS CLI プロファイル名 |
| `CDK_DEFAULT_ACCOUNT` | デプロイ先の AWS アカウント ID |
| `CDK_DEFAULT_REGION` | デプロイ先リージョン (例: `ap-northeast-1`) |

### 2. Python 仮想環境を作成してライブラリをインストールする

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## デプロイ

### 特定のスタックだけデプロイする

```bash
cdk deploy <StackName>
```

| コマンド | 対象 |
|---------|------|
| `cdk deploy CdkEc2Stack` | EC2 インスタンス |
| `cdk deploy CdkLambdaStack` | Lambda + Function URL |
| `cdk deploy CdkRdsStack` | RDS PostgreSQL |
| `cdk deploy CdkApiLambdaStack` | Lambda + API Gateway |
| `cdk deploy CdkElasticBeanstalkStack` | Elastic Beanstalk (Ruby on Rails + PostgreSQL) |

### すべてのスタックをデプロイする

```bash
cdk deploy --all
```

### 初回のみ bootstrap が必要な場合

```bash
cdk bootstrap
```

## デプロイ前の確認

いきなり `cdk deploy` せず、次の順で確認するのが安全です。

```bash
# CloudFormation テンプレート生成の確認
cdk synth <StackName>

# AWS との差分確認
cdk diff <StackName>
```

## 各スタックの詳細

### EC2 スタック (`CdkEc2Stack`)

- インスタンスタイプ: `t3.micro`
- OS: Amazon Linux 2023
- VPC: default VPC を再利用
- 接続方法: SSM Session Manager (SSH キー不要)

### Lambda スタック (`CdkLambdaStack`)

- ランタイム: Python 3.13
- エンドポイント: Lambda Function URL (API Gateway 不要)
- 認証: なし (`NONE`) — 必要に応じて `AWS_IAM` に変更
- タイムアウト: 30 秒
- デプロイ後の Output: `FunctionUrl`

動作確認:

```bash
curl <FunctionUrl>
# => {"message": "Hello from Lambda!"}
```

### RDS スタック (`CdkRdsStack`)

- エンジン: PostgreSQL 17
- インスタンスタイプ: `db.t3.micro`
- VPC: default VPC のパブリックサブネット
- 認証情報: Secrets Manager 自動生成
- データベース名: `appdb`
- ストレージ: 20GB (gp2)

デプロイ後の Output:

| Output | 内容 |
|--------|------|
| `DbEndpoint` | 接続エンドポイント |
| `DbPort` | ポート番号 (5432) |
| `DbSecretArn` | Secrets Manager の ARN |

パスワードの取得:

```bash
aws secretsmanager get-secret-value \
  --secret-id <DbSecretArn> \
  --query SecretString \
  --output text
```

### Lambda + API Gateway スタック (`CdkApiLambdaStack`)

- ランタイム: Python 3.13
- エンドポイント: API Gateway REST API (`GET /`)
- Function URL は発行しない
- タイムアウト: 30 秒

デプロイ後の Output:

| Output | 内容 |
|--------|------|
| `ApiUrl` | API Gateway エンドポイント URL |

動作確認:

```bash
curl <ApiUrl>
# => {"message": "Hello from Lambda!"}
```

### Elastic Beanstalk スタック (`CdkElasticBeanstalkStack`)

Ruby on Rails (PostgreSQL) アプリのデプロイを想定した構成です。

- プラットフォーム: Ruby 3.3 on Amazon Linux 2023
- 環境タイプ: LoadBalanced (ALB + Auto Scaling)
- インスタンスタイプ: `t3.micro`
- VPC: default VPC のパブリックサブネット

**RDS PostgreSQL:**

- エンジン: PostgreSQL 17
- インスタンスタイプ: `db.t3.micro`
- データベース名: `app_production`
- 認証情報: Secrets Manager 自動生成
- EB インスタンスからのみ 5432 番ポートへのアクセスを許可

**EB インスタンスに渡される環境変数:**

| 変数名 | 内容 |
|--------|------|
| `RAILS_ENV` | `production` |
| `DATABASE_HOST` | RDS エンドポイント |
| `DATABASE_PORT` | `5432` |
| `DATABASE_NAME` | `app_production` |
| `DATABASE_SECRET_ARN` | Secrets Manager の ARN (パスワード取得に使用) |

> DB パスワードは `DATABASE_SECRET_ARN` 経由で Secrets Manager から取得する設計です。
> Rails アプリ側で `aws-sdk-secretsmanager` gem などを使って `DATABASE_URL` を組み立ててください。

デプロイ後の Output:

| Output | 内容 |
|--------|------|
| `EbEndpointUrl` | EB 環境のエンドポイント URL |
| `DbEndpoint` | RDS 接続エンドポイント |
| `DbSecretArn` | Secrets Manager の ARN |

> **注意**: `solution_stack_name` は変更されることがあります。最新バージョンは以下で確認してください。
> ```bash
> aws elasticbeanstalk list-available-solution-stacks \
>   --query "SolutionStacks[?contains(@, 'Ruby')]"
> ```

### CdkDurableLambdaStack

- ランタイム: Python 3.13
- Durable Functions を有効化（チェックポイント/リプレイ機能付き）
- `execution_timeout`: 最大 1 時間のワークフロー実行
- `retention_period`: 実行履歴を 7 日間保持
- `prod` エイリアスを作成（呼び出しには修飾 ARN が必須）

> ⚠️ **制約事項**
> - 現時点では利用可能リージョンが限られます (us-east-2 など)
> - 既存の Lambda 関数には後から有効化できません（新規作成時のみ）
> - デプロイ前に SDK のインストールが必要です:
>   ```bash
>   pip install -r lambda_durable/requirements.txt -t lambda_durable/
>   ```

デプロイ後の Output:

| Output | 内容 |
|--------|------|
| `FunctionAliasArn` | 呼び出しに使用する修飾 ARN (`prod` エイリアス) |

## 削除

```bash
cdk destroy <StackName>
# または全スタック
cdk destroy --all
```

> **注意**: RDS スタックは `RemovalPolicy.DESTROY` のためスタック削除時に DB も削除されます。本番環境では `RETAIN` に変更してください。

## 秘匿情報の扱い

- `.env` には `AWS_PROFILE` / `CDK_DEFAULT_ACCOUNT` / `CDK_DEFAULT_REGION` を記載する
- `.env` は Git にコミットしない (`.gitignore` で除外済み)
- 共有用テンプレートは `.env.example` を使う
- 新しい環境変数を追加したら `.env.example` にもキーだけ追加する

## スタックの追加方法

新しい AWS リソースを追加する場合の手順:

1. `cdk_<service>_stack.py` を作成し、スタッククラスを定義する
2. `app.py` に import とインスタンス化を追加する
3. 必要であれば `lambda/` などリソースのコードを追加する
4. `cdk synth <StackName>` で動作確認する
5. `.github/skills/` に対応するスキル (`SKILL.md`) を追加する

## よくある詰まりどころ

### default VPC が見つからない

- 指定リージョンに default VPC が存在するか確認する
- `.env` の `CDK_DEFAULT_REGION` が正しいか確認する

### `aws_cdk` が import できない

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### `cdk` コマンドはあるが Python 側で失敗する

CDK CLI と Python ライブラリは別管理です。両方のインストールを確認してください。


このプロジェクトでは次の方針を取っています。

- EC2 は 1 台だけ作る
- 新しい VPC は作らない
- 既存の default VPC を使う
- 環境変数は `.env` で管理する
- `.env` は `python-dotenv` で自動読み込みする

CDK を初めて触る人でも、README を上から順に読めばセットアップからデプロイ前確認まで進められるようにしています。

## この構成で作成されるもの

- EC2 インスタンス 1 台
- インスタンス用の周辺リソース
  - IAM ロール
  - セキュリティグループ

このプロジェクトでは VPC 自体は作成しません。EC2 は AWS の仕様上、必ず何らかの VPC に属する必要があるため、既存の default VPC を参照します。

## 前提条件

このプロジェクトを使う前に、次を満たしている必要があります。

- Python 3 がインストールされている
- AWS CDK CLI がインストールされている
- AWS CLI などで認証済みである
- デプロイ先アカウント・リージョンに default VPC が存在する

参考コマンド:

```bash
python3 --version
cdk --version
aws sts get-caller-identity
```

## ファイル構成

主要ファイルは次の通りです。

- `app.py`
  - CDK アプリのエントリーポイント
  - `.env` を読み込んでスタックを起動する
- `stacks/cdk_ec2_stack.py`
  - EC2 を 1 台作るスタック定義
- `requirements.txt`
  - Python 依存ライブラリ一覧
- `cdk.json`
  - CDK CLI がアプリを起動するための設定
- `.env.example`
  - ローカル用 `.env` の雛形
- `.gitignore`
  - `.env` や仮想環境などを Git 管理から除外する

## 秘匿情報の扱い

ローカル固有の情報や、漏れるとセキュリティ・プライバシー上のリスクがある値は `.env` に置いてください。

例:

- `AWS_PROFILE`
- `CDK_DEFAULT_ACCOUNT`
- `CDK_DEFAULT_REGION`
- 将来的に使う API キーやトークン

運用ルールは次です。

- `.env` は Git にコミットしない
- 共有用のテンプレートは `.env.example` を使う
- 新しい環境変数を追加したら、`.env.example` にもキーだけ追加する

## セットアップ手順

### 1. `.env` を作成する

```bash
cp .env.example .env
```

`.env` の例:

```dotenv
AWS_PROFILE=kura-dev
CDK_DEFAULT_ACCOUNT=123456789012
CDK_DEFAULT_REGION=ap-northeast-1
```

各値の意味:

- `AWS_PROFILE`
  - 利用する AWS CLI プロファイル名
- `CDK_DEFAULT_ACCOUNT`
  - デプロイ対象の AWS アカウント ID
- `CDK_DEFAULT_REGION`
  - デプロイ対象リージョン

### 2. Python 仮想環境を作成する

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 依存ライブラリをインストールする

```bash
pip install -r requirements.txt
```

このプロジェクトで主に使っているライブラリ:

- `aws-cdk-lib`
- `constructs`
- `python-dotenv`

## このプロジェクトの実装内容

スタック定義は `stacks/cdk_ec2_stack.py` にあります。

やっていることはシンプルです。

1. 既存の default VPC を参照する
2. EC2 インスタンスを 1 台作成する
3. Amazon Linux 2023 を使う
4. インスタンスタイプは `t3.micro` を使う
5. SSM Session Manager で接続しやすいように権限を付ける

つまり、SSH キーの事前配布よりもまず「1 台を作ること」を優先した最小構成です。

## 実行前に確認するとよいコマンド

いきなり `cdk deploy` せず、次の順で確認するのが安全です。

### CDK アプリのテンプレート生成

```bash
cdk synth
```

これで CloudFormation テンプレートが生成できれば、少なくとも CDK アプリとしては成立しています。

### 差分確認

```bash
cdk diff
```

これで AWS に何が作成されるかをデプロイ前に確認できます。

## デプロイ

初回は bootstrap が必要な場合があります。

```bash
cdk bootstrap
cdk deploy
```

補足:

- `cdk bootstrap` は CDK がデプロイ時に必要とするリソースを準備します
- すでに対象アカウント・リージョンで bootstrap 済みなら毎回は不要です

## 削除

不要になったら次で削除できます。

```bash
cdk destroy
```

## よくある詰まりどころ

### default VPC が見つからない

原因:

- 指定リージョンに default VPC が存在しない
- `CDK_DEFAULT_REGION` が想定と違う

確認ポイント:

- AWS マネジメントコンソールで default VPC の存在を確認する
- `.env` のリージョン値が正しいか見る

### `aws_cdk` が import できない

原因:

- 仮想環境が有効化されていない
- 依存がまだ入っていない

対処:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### `cdk` コマンドはあるが Python 側で失敗する

原因:

- CDK CLI と Python ライブラリは別管理だから

対処:

- `cdk --version` だけで安心しない
- `pip install -r requirements.txt` も必ず実施する

## Git 運用

このディレクトリは Git リポジトリとして初期化できます。

運用上の注意:

- `.env` はコミットしない
- `.env.example` はコミットする
- まず `cdk synth` や `cdk diff` で内容を確認してから `cdk deploy` する

## 今後拡張するとしたら

この README 時点では、あえて最小構成に留めています。

将来的には次の拡張が考えられます。

- キーペア指定
- 固定のセキュリティグルールール追加
- EBS サイズ変更
- タグ追加
- User Data で初期化スクリプト投入
- インスタンスタイプや AMI の外部設定化

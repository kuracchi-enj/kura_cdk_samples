# cdk_ec2

AWS CDK Python を使って、EC2 インスタンスを 1 台だけ作るための最小構成です。

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
- `cdk_ec2_stack.py`
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

スタック定義は `cdk_ec2_stack.py` にあります。

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

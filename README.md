# cdk_ec2

AWS CDK Python で EC2 を 1 台だけ作る最小構成です。
新しい VPC は作らず、既存の default VPC を参照します。

## 前提

- Python 3
- AWS CDK CLI
- AWS 認証済みプロファイル
- 対象アカウント・リージョンに default VPC が存在する

## 秘匿情報の扱い

- ローカル固有の認証情報やアカウント情報は `.env` に入れて管理する
- `.env` は Git に含めない
- 共有用の雛形は `.env.example` を使う

## セットアップ

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## デプロイ

```bash
cdk bootstrap
cdk deploy
```

## 削除

```bash
cdk destroy
```

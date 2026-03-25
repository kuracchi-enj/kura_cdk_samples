from aws_durable_execution_sdk_python import DurableContext, durable_execution


@durable_execution
def handler(event: dict, context: DurableContext):
    """
    Durable Function のサンプルハンドラー。

    step() でチェックポイントを作成しながら順番に処理を進める。
    wait() の間はコンピュートチャージが発生しない。

    呼び出しには必ずバージョン/エイリアスの修飾 ARN を使うこと。
    例: arn:aws:lambda:<region>:<account>:function:durable-hello:prod
    """
    # step 1: 最初の処理（失敗した場合は自動リトライ・リプレイされる）
    result1 = context.step(
        lambda _: {"message": f"Hello, {event.get('name', 'World')}!"},
        name="greet",
    )

    # wait: 5 秒間コンピュートなしで待機（デモ用の短い待機時間）
    context.wait(seconds=5)

    # step 2: 後続の処理
    result2 = context.step(
        lambda _: {**result1, "status": "completed"},
        name="finalize",
    )

    return result2

FROM public.ecr.aws/lambda/python:3.13

# 依存関係を個別にインストール
RUN pip install --no-cache-dir \
    slack-bolt==1.23.0 \
    slack-sdk==3.35.0 \
    boto3==1.35.36

# アプリケーションコードのコピー
COPY src/ ${LAMBDA_TASK_ROOT}/

# ハンドラーの指定
CMD ["lambda_function.lambda_handler"]
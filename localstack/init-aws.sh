#!/bin/bash
# LocalStack 啟動完成後自動執行（掛載到 /etc/localstack/init/ready.d/）
# 建立：analyze-queue → analyzer → SNS comment-analyzed → db-writer-queue / stats-queue
# 每個 queue 都有自己的 DLQ，失敗 MAX_RECEIVE 次後移入
set -euo pipefail

MAX_RECEIVE=3
VISIBILITY_TIMEOUT=60

# 建立 queue 並回傳 URL
create_queue() {
  awslocal sqs create-queue --queue-name "$1" ${2:+--attributes "$2"} --query QueueUrl --output text
}

# 由 queue URL 查詢 ARN（不自行拼接，避免寫死帳號 ID）
queue_arn() {
  awslocal sqs get-queue-attributes --queue-url "$1" \
    --attribute-names QueueArn --query Attributes.QueueArn --output text
}

create_queue_with_dlq() {
  local name="$1"
  local dlq_arn
  dlq_arn=$(queue_arn "$(create_queue "${name}-dlq")")
  create_queue "${name}" "{
    \"VisibilityTimeout\": \"${VISIBILITY_TIMEOUT}\",
    \"RedrivePolicy\": \"{\\\"deadLetterTargetArn\\\":\\\"${dlq_arn}\\\",\\\"maxReceiveCount\\\":\\\"${MAX_RECEIVE}\\\"}\"
  }" >/dev/null
  echo "queue ready: ${name} (dlq: ${name}-dlq)"
}

create_queue_with_dlq analyze-queue
create_queue_with_dlq db-writer-queue
create_queue_with_dlq stats-queue

topic_arn=$(awslocal sns create-topic --name comment-analyzed --query TopicArn --output text)
echo "topic ready: comment-analyzed"

# RawMessageDelivery=true：consumer 直接收到原始 JSON，不用再拆 SNS 外層包裝
for q in db-writer-queue stats-queue; do
  q_arn=$(queue_arn "$(awslocal sqs get-queue-url --queue-name "${q}" --query QueueUrl --output text)")
  awslocal sns subscribe \
    --topic-arn "${topic_arn}" \
    --protocol sqs \
    --notification-endpoint "${q_arn}" \
    --attributes RawMessageDelivery=true >/dev/null
  echo "subscribed: ${q} -> comment-analyzed"
done

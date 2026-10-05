# 2026_Kotoba_Lab

## 本機啟動

### 1. 建立 secrets 檔案

`secrets/` clone 後需自行建立以下檔案（內容為單行純文字，結尾不要換行）：

| 檔案 | 用途 | 內容 |
|---|---|---|
| `secrets/db_username.txt` | PostgreSQL 帳號 | 自訂 |
| `secrets/db_password.txt` | PostgreSQL 密碼 | 自訂 |
| `secrets/redis_password.txt` | Redis（Valkey）密碼 | 自訂 |
| `secrets/aws_access_key_id.txt` | 連 LocalStack 用 | 自訂 |
| `secrets/aws_secret_access_key.txt` | 連 LocalStack 用 | 自訂 |

```bash
mkdir -p secrets
printf '<帳號>' > secrets/db_username.txt
printf '<密碼>' > secrets/db_password.txt
printf '<密碼>' > secrets/redis_password.txt
printf '<任意非空值>' > secrets/aws_access_key_id.txt
printf '<任意非空值>' > secrets/aws_secret_access_key.txt
```

> AWS 的兩個檔案只在本機連 LocalStack 時使用（LocalStack 不驗證帳密，但需要非空值來辨識帳號與 region）。
> 部署到 AWS 時不使用這兩個檔案，帳密由 IAM Role 提供。

### 2. 啟動

```bash
docker compose up --build -d
docker compose ps -a
```

全部啟動完成後（約 30 秒）：

| 服務 | 預期狀態 |
|---|---|
| `postgres`、`redis`、`localstack` | healthy |
| `migrate` | Exited (0)（建立資料表後結束） |
| `app`、`analyzer`、`db-writer`、`stats-writer` | healthy |

API：<http://localhost:8000/health>

### 3. 送一則測試訊息

```bash
docker compose run --rm --no-deps -T --entrypoint /venv/bin/python app -m scripts.send_test_message
docker compose logs analyzer db-writer stats-writer --since 1m
```

### 停止

```bash
docker compose down      # 保留資料庫資料
docker compose down -v   # 連資料庫資料一起清除
```

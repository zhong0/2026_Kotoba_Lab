# Chainguard distroless Python（Wolfi 系，以維持 0 CVE 為目標滾動修補）
# 需要 RHEL 系基底的環境改用 Dockerfile.rocky
FROM cgr.dev/chainguard/python:latest-dev AS builder
# 只在 build 階段用 root；runtime 仍以 nonroot 執行
USER root

WORKDIR /app
COPY requirements.txt .
RUN python -m venv /venv && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt && \
    /venv/bin/pip uninstall -y pip

# runtime 不含 shell 與套件管理器，攻擊面最小
FROM cgr.dev/chainguard/python:latest

WORKDIR /app
COPY --from=builder /venv /venv
# 預設使用者是 nonroot (uid 65532)；log 一律寫 stdout，程式目錄不需可寫
COPY . .

EXPOSE 8000

ENTRYPOINT ["/venv/bin/python", "main.py"]

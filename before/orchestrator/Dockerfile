# The orchestrator runs as a container in the platform compose stack.
# It shells out to a LOCAL agent runner (default: goose) pointed at Ollama —
# no cloud, no proprietary SDK.
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y git pipx curl && rm -rf /var/lib/apt/lists/*

# Install the local agent runner(s). Default is goose; aider is the alternative.
# (Pick what your AGENT_RUNNER selects; both talk to Ollama.)
RUN pipx install aider-chat || true
RUN curl -fsSL https://raw.githubusercontent.com/block/goose/main/download_cli.sh | bash || true
ENV PATH="/root/.local/bin:${PATH}"

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Not always-on: invoke per feature with
#   docker compose run --rm -e CC_BRIEF="..." -e OLLAMA_MODEL=qwen2.5-coder:14b orchestrator
CMD ["python", "run.py"]

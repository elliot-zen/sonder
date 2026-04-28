# Sonder

Sonder is a small local agent runtime with a CLI transport and a gateway process for chat platforms.

## Requirements

- Python 3.13+
- uv

## Install

```bash
uv sync
```

## CLI

Run the local terminal UI:

```bash
uv run sonder
```

The CLI uses Rich for output and prompt-toolkit for input editing, including better Chinese text handling.

## Gateway

Remote chat platforms are started through one gateway process:

```bash
uv run sonder-gateway
```

The gateway reads config from:

```text
~/.sonder/config.toml
```

Create one from the example:

```bash
mkdir -p ~/.sonder
cp gateway.toml.example ~/.sonder/config.toml
```

Current Telegram config:

```toml
[telegram]
enabled = true
bot_token = "123456:replace-with-your-bot-token"
allowed_users = ["123456789"]
```

`allowed_users` should contain your Telegram user id as a string. Users not in the list receive `Unauthorized`.

You can also test with an explicit config path:

```bash
uv run sonder-gateway --config gateway.toml.example
```

## Security Notes

- The Telegram bot token is read directly from `~/.sonder/config.toml`; keep that file private.
- The default tool is `Bash`, which can execute shell commands on your machine.
- Use `allowed_users` for Telegram before leaving the gateway running.
- Logs redact Telegram Bot API token URLs and reduce noisy HTTP client logs.

If a bot token was printed or shared accidentally, revoke and regenerate it in BotFather.

## Architecture

```text
src/sonder/
├── gateway/      # gateway config and remote chat entrypoint
├── transports/   # CLI and Telegram adapters
├── runtime/      # agent loop and tool-call orchestration
├── llm/          # LLM provider abstraction and OpenAI-compatible provider
├── tools/        # Bash tool and registry
├── storage/      # in-memory session store
└── types.py      # Pydantic models shared across layers
```

Transport adapters translate platform messages into runtime calls. The agent runtime does not know whether a message came from CLI or Telegram.

## Logging

Gateway logs use the standard format:

```text
YYYY-MM-DD HH:MM:SS LEVEL [logger.name] message
```

Telegram incoming messages are logged with a short preview. Long messages are truncated and newlines are normalized.

## Tests

```bash
uv run python -m unittest discover -s tests -v
uv run python -m compileall src tests
```

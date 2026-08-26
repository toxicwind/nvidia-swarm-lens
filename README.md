# 🔮 huh

Moonbox swarm orchestration with Mintlify MCP integration.

## Machine
- **Name:** redwood
- **Meta:** extreme
- **Mode:** YOLO

## Structure
```
huh/
├── .env              # API keys (gitignored)
├── .gitignore
├── README.md
├── skills/           # Browser automation & MCP skills
├── configs/          # Project manifests & MCP configs
├── bin/              # Portable binary loaders
├── references/       # Research docs
└── logs/             # Runtime logs
```

## Quick Start
```bash
bash setup.sh
python loader.py load
python loader.py test
```

## MCP Servers
| Server | Status | URL |
|--------|--------|-----|
| Mintlify | ✅ | https://mcp.mintlify.com |
| Context7 | ⚠️ | https://mcp.context7.com/mcp |
| Exa | ❌ | X402_PAYMENT_REQUIRED |

## Skills
- `fast-browser-use` — Research-grade Cloudflare bypass (nodriver, Patchright, Camoufox, curl_cffi)

## License
AGPL-3.0

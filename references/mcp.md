# KAUCHE MCP server

Exposes KAUCHE as MCP tools for Claude Desktop, Claude Code, or any MCP client.

## Install & run

```bash
pip install mcp              # the MCP SDK
# from the repo root (so `kauche` is importable):
python3 -m kauche.mcp_server       # stdio transport
```

Or install the package to get the `kauche-mcp` command:

```bash
pip install -e ".[mcp]"
kauche-mcp
```

## Client config

Claude Desktop (`claude_desktop_config.json`) or Claude Code (`.mcp.json`):

```json
{
  "mcpServers": {
    "kauche": {
      "command": "python3",
      "args": ["-m", "kauche.mcp_server"],
      "cwd": "/absolute/path/to/kauche-skill"
    }
  }
}
```

## Tools

| Tool | Auth | What |
|---|---|---|
| `kauche_deals` | none | today's daily-sale collections + products |
| `kauche_collections` | none | list sale/campaign collections (optional `grep`) |
| `kauche_collection_products` | none | products in a collection |
| `kauche_product` | none (+login for reviews) | product detail; `with_reviews` adds rating/reviews |
| `kauche_reviews` | anon | reviews + aggregate rating for a product gid |
| `kauche_timesale` | anon | home time-sale products |
| `kauche_categories` | anon | product categories |
| `kauche_coupons` | anon | session coupons |
| `kauche_sales_ranking` | login | best sellers |
| `kauche_new_arrivals` | login | newest products |
| `kauche_shop_products` | login | a seller's products |
| `kauche_api` | varies | call any Connect-RPC method (`kauche-endpoints.txt`) |
| `kauche_login` | — | returns a sign-in URL; user opens it, token saved securely |
| `kauche_whoami` / `kauche_logout` | — | session state / clear |

## Login flow (token never shown)

1. A login-gated tool returns `{"status":"login_required"}`.
2. Call `kauche_login` → returns `{"login_url": "http://127.0.0.1:PORT/"}`.
3. The user opens that URL, signs in with Google/Apple; the token is written to
   `~/.cache/kauche-api/account.json` (chmod 600). It is never returned to the client.
4. Call `kauche_whoami` to confirm, then retry the gated tool. Auto-refreshed thereafter;
   on expiry the gated tools return `login_required` again.

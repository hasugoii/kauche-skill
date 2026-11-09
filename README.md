# kauche-skill

An [Agent Skill](https://agentskills.io) that lets any AI agent (Claude Code, Codex,
Cursor, OpenCode, …) browse the Japanese shopping app **KAUCHE (カウシェ)** —
daily deals, coupon collections, Kauche-Farm target products, product details and
app share links — and answer questions about how the app works.

KAUCHE has no web shop and no public API. Its catalog is a Shopify store whose
standard storefront JSON is public; this skill wraps it (read-only, no login) and
documents the app's rules from the official FAQ. Purchases still happen in the app.

## First run (for agents)

After you clone this, most commands work immediately (anonymous session): catalog,
prices, deals, reviews, time sale, categories. For **account-gated** data (sales ranking,
new arrivals, product detail, the user's own listings) the CLI returns a "needs login"
message — when that happens, **ask the user** to run:

```bash
python3 scripts/kauche.py login
```

That opens their browser to sign in with Google/Apple; the token is saved and refreshed
automatically. Don't attempt to log in for them. `python3 scripts/kauche.py whoami` shows
the current state. See `SKILL.md` → "Setup when you pull this skill".

## Install

Claude Code (personal skill):

```bash
git clone https://github.com/hasugoii/kauche-skill ~/.claude/skills/kauche
```

Project skill: clone into `.claude/skills/kauche` inside the repo. Other agents
that follow the Agent Skills spec read `SKILL.md` from their own skills folder,
e.g. `~/.codex/skills/kauche` or `.cursor/skills/kauche`. Or just run the CLI:

```bash
python3 scripts/kauche.py deals
python3 scripts/kauche.py product https://kauche.com/products/<handle>
python3 scripts/kauche.py farm-targets --json
```

Requires Python 3.9+ only. Responses are cached 10 min in `~/.cache/kauche-skill`.

## Layout

| Path | Purpose |
|---|---|
| `SKILL.md` | instructions the agent loads (what it can/can't do, rules, workflows) |
| `scripts/kauche.py` | CLI: `collections`, `products`, `product`, `search`, `deals`, `farm-targets`, `link`, `raw` |
| `references/storefront-api.md` | endpoints, JSON shape, collection naming, rate limits |
| `references/kauche-app.md` | app features, coins/coupons, farm mechanics, seller fees, official URLs |
| `notes/portal-notes.md` | traps found while reverse-engineering; append new ones |

## Limits (read before relying on it)

- Shopify throttles hard: ~10 quick requests ⇒ `429` for several minutes. The CLI paces
  and caches; don't crawl.
- Predictive search returns `417 Unsupported buyer locale` on this shop, so `search`
  is best-effort; filter a collection locally instead.
- Prices/stock are a public mirror; the app may differ. Share links
  (`https://kauche.com/products/<handle>`) open the product in the app.
- Not affiliated with KAUCHE, Inc. Respect their ToS; this is for personal shopping
  assistance and research, not scraping at scale.

## Tiếng Việt

Skill này cho phép agent xem catalog Kauche (deal theo ngày, bộ sưu tập coupon, sản
phẩm đổi được bằng coupon Farm, chi tiết sản phẩm) qua Shopify storefront công khai,
và trả lời cách app hoạt động (coin, coupon, farm, phí bán hàng). Không mua được từ
đây: mua trong app bằng share link. Chi tiết bẫy xem `notes/portal-notes.md`.

License: MIT.

## Internal API (v0.2)

Beyond the Shopify storefront, this now wraps KAUCHE's **internal Connect-RPC API**
(`api.kauche.com`), reverse-engineered from the Android app v2.164.0:

- Anonymous Firebase auth (no signup) — `kauche/auth.py`.
- Browser login: `kauche login` opens a link, you sign in with Google/Apple, the token
  returns automatically — `kauche/weblogin.py`. Headless alternatives: `--refresh-token`,
  `--google-id-token`, `--custom-token` (LINE).
- Reviews & ratings, home time sale, product categories, coupons: verified working.
- Sales ranking / new arrivals / GetProduct: mapped, but need a signed-in user (return
  `code 13` anonymously).
- Full endpoint list in `references/kauche-endpoints.txt`; map + field schemas in
  `references/internal-api.md`.

```python
from kauche import Kauche
k = Kauche()
k.time_sale()
k.reviews("gid://shopify/Product/15426646638760")
```

Read-only. Not affiliated with KAUCHE, Inc. Respect their ToS; for personal shopping
assistance and research, not large-scale scraping.


## MCP server

Use KAUCHE from Claude Desktop / Claude Code / any MCP client:

```bash
pip install mcp
python3 -m kauche.mcp_server        # stdio
```

Tools: `kauche_deals`, `kauche_collections`, `kauche_product`, `kauche_reviews`,
`kauche_timesale`, `kauche_categories`, `kauche_sales_ranking`, `kauche_shop_products`,
`kauche_api`, `kauche_login`, `kauche_whoami`. The `kauche_login` tool returns a browser
sign-in URL and captures the token locally (never returned to the client). Config and
details in `references/mcp.md`.

from dataclasses import dataclass


@dataclass(frozen=True)
class Board:
    source: str
    slug: str
    company: str


# Public job-board APIs these companies publish for their own careers pages.
BOARDS: list[Board] = [
    Board("greenhouse", "groww", "Groww"),
    Board("greenhouse", "rubrik", "Rubrik"),
    Board("greenhouse", "databricks", "Databricks"),
    Board("greenhouse", "cloudflare", "Cloudflare"),
    Board("greenhouse", "mongodb", "MongoDB"),
    Board("greenhouse", "gitlab", "GitLab"),
    Board("greenhouse", "stripe", "Stripe"),
    Board("greenhouse", "twilio", "Twilio"),
    Board("greenhouse", "coinbase", "Coinbase"),
    Board("greenhouse", "airbnb", "Airbnb"),
    Board("greenhouse", "figma", "Figma"),
    Board("greenhouse", "dropbox", "Dropbox"),
    Board("greenhouse", "okta", "Okta"),
    Board("greenhouse", "inmobi", "InMobi"),
    Board("greenhouse", "glance", "Glance"),
    Board("greenhouse", "hackerrank", "HackerRank"),
    Board("greenhouse", "observeai", "Observe.AI"),
    Board("greenhouse", "truefoundry", "TrueFoundry"),
    Board("greenhouse", "elastic", "Elastic"),
    Board("greenhouse", "datadog", "Datadog"),
    Board("greenhouse", "druva", "Druva"),
    Board("greenhouse", "zscaler", "Zscaler"),
    Board("greenhouse", "anthropic", "Anthropic"),
    Board("greenhouse", "vercel", "Vercel"),
    Board("lever", "meesho", "Meesho"),
    Board("lever", "cred", "CRED"),
    Board("lever", "zeta", "Zeta"),
    Board("lever", "paytm", "Paytm"),
    Board("lever", "spotify", "Spotify"),
    Board("lever", "palantir", "Palantir"),
    Board("lever", "fampay", "FamPay"),
    Board("lever", "mindtickle", "Mindtickle"),
    Board("ashby", "notion", "Notion"),
    Board("ashby", "linear", "Linear"),
    Board("ashby", "openai", "OpenAI"),
    Board("ashby", "ramp", "Ramp"),
    Board("ashby", "sarvam", "Sarvam AI"),
    Board("ashby", "deel", "Deel"),
    Board("ashby", "replit", "Replit"),
    Board("ashby", "perplexity", "Perplexity"),
    Board("ashby", "atlan", "Atlan"),
    Board("ashby", "composio", "Composio"),
    Board("ashby", "snowflake", "Snowflake"),
]

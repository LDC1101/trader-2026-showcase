# data/

Runtime directory, ignored by git except for this file. The scripts write state files,
logs, quote caches and downloaded price history here (for example `watch_state.json`,
`watch.log`, `daily_state.json`, `sg_quotes.json`, `brent.csv`). The research scripts in
`src/` print which file they need and how it was fetched when it is missing.

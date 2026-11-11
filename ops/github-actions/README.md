# GitHub Actions

`buy-alert.yml` is the reference copy of the buy alert that ran during the season
(16 Oct to 23 Oct 2026 with a live config, disabled on 11 Nov 2026). It lives here and not in
`.github/workflows/` so that it never runs from this repo.

To use it in a fork: move it to `.github/workflows/`, add the repository secrets
`TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`, commit a `depot/buy_alert.json` (see
`depot/examples/buy_alert.json`), and start with
`gh workflow run buy-alert.yml -f mode=probe`, which prints the alert without sending it.

The only workflow that runs here is `.github/workflows/tests.yml`.

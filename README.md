# iBOOD Poller

This repository contains a set of Python scripts to poll the iBOOD website for deals.

## Usage

### Hunt Fetcher

To run the hunt fetcher, use the following command:

```bash
uv run ibood_hunt_fetcher
```

### All Deals Fetcher

To run the all deals fetcher and send an email with the deals, use the following command:

```bash
GMAIL_USERNAME="" GMAIL_APP_PASSWORD="" GMAIL_RECIPIENT="" uv run ibood_all_deals_fetcher --keywords keywords.txt --send-email
```

**Note:** You need to replace the values for `GMAIL_USERNAME`, `GMAIL_APP_PASSWORD`, and `GMAIL_RECIPIENT` with your own credentials. You also need to have a `keywords.txt` file in the same directory with a list of keywords to filter the deals.

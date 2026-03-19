import requests
import json
import structlog
import argparse
import os
import smtplib
import time
import random
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from textwrap import dedent
from typing import List

from ._logging import _setup_logging
from .ibood_api.api_client import IboodClient
from .ibood_api.models import IboodDeal
from .deal_history import DealHistory

# Configure structlog
_setup_logging()
logger = structlog.get_logger()

def generate_html_report(new_deals: List[IboodDeal], other_deals: List[IboodDeal]) -> str:
    """Generates an email-compatible HTML report using an inline-block layout."""

    deals = new_deals + other_deals
    deal_count = len(deals)
    styles = dedent("""
        body { font-family: sans-serif; }
        .deal-container { text-align: center; }
        .deal { 
            display: inline-block; 
            box-sizing: border-box; 
            padding: 1em; 
            margin: 0.25%; 
            width: 24%; 
            background: #eee; 
            border: 1px #aaa solid; 
            border-radius: 3px; 
            vertical-align: top; 
            text-align: center; 
        }
        .deal img { max-width: 100%; height: 180px; max-height: 180px; object-fit: contain; }
        .deal h3 { margin-top: 0; font-size: 16px; height: 50px; overflow: hidden; text-overflow: ellipsis; }
        .deal p { margin: 4px 0; font-size: 14px; }
        .keywords { font-style: italic; color: #555; font-size: 0.9em; }
        .deal-brand { font-weight: normal; color: #333; }
        .deal-price { font-weight: bold; color: #d9534f; font-size: 1.1em; }
        @media only screen and (max-width: 768px) { 
            .deal { width: 99% !important; margin: 1%; } 
        }
    """)

    deal_cards_html = []
    for deal in deals:
        is_new = deal in new_deals
        card_style = "background: #d9edf7;" if is_new else "background: #eee;"
        keywords_joined = ", ".join(deal.matched_keywords)

        title_html = f"<a href='{deal.url}' style='color: #000; text-decoration: none;'>{deal.title}</a>" if deal.url else deal.title
        image_html = ""
        if deal.image:
            image_html = f"<img src='{deal.image}' alt='{deal.title}'>"
            if deal.url:
                image_html = f"<a href='{deal.url}'>{image_html}</a>"

        deal_cards_html.append(dedent(f"""
            <div class='deal' style='{card_style}'>
                {image_html}
                <h3>{title_html}</h3>
                <p class='deal-price'>{deal.price}</p>
            </div>
        """))

    deals_html = "".join(deal_cards_html)

    return dedent(f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name='viewport' content='width=device-width, initial-scale=1.0'>
            <style>{styles.strip()}</style>
        </head>
        <body>
            <h2>iBOOD Daily Deals Report ({deal_count} deals)</h2>
            <div class='deal-container'>
                {deals_html}
            </div>
        </body>
        </html>
    ''')

def send_email(html_content: str, sender_email: str, recipient_email: str, app_password: str, deal_count: int):
    """Sends an HTML email using Gmail's SMTP server."""
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"iBOOD Daily Deals Report: {deal_count} deals found"
    msg['From'] = sender_email
    msg['To'] = recipient_email

    part = MIMEText(html_content, 'html')
    msg.attach(part)

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
            logger.info("Email sent successfully!")
    except smtplib.SMTPException as e:
        logger.error("Failed to send email", error=str(e))

def fetch_and_process_deals(keywords: List[str], send_email_flag: bool):
    """
    Fetches all deals, filters them, and optionally sends an email.
    """
    client = IboodClient()
    deal_history = DealHistory("__cache__/all_deals_history.json")

    try:
        response = client.get_all_deals()
        response.raise_for_status()
        logger.info("API request", status_code=response.status_code)

        data = response.json()
        items = data.get("data", {}).get("items", [])
        if not items:
            logger.warning("No items found in response")
            return
        
        logger.info(f"Found {len(items)} deals from API")

        # Convert all items to IboodDeal objects first
        all_deals = []
        for item in items:
            try:
                deal = IboodDeal.from_dict(item)
                all_deals.append(deal)
            except KeyError as e:
                logger.warning("Could not parse deal, missing key", key=str(e), deal_data=item)

        # Filter deals by keywords
        matched_deals = []
        if keywords:
            for deal in all_deals:
                deal.find_and_store_matches(keywords)
                if deal.matched_keywords:
                    matched_deals.append(deal)
            logger.info(f"Found {len(matched_deals)} deals matching keywords")
        else:
            # If no keywords, all deals are considered "matched" for history
            matched_deals = all_deals

        # Update deal history with the matched IboodDeal objects
        deal_history.update(matched_deals)
        deal_history.cleanup_old_deals()
        
        # Sort and categorize the matched deals
        keyword_map = {kw: i for i, kw in enumerate(keywords)}
        new_deals = []
        other_deals = []

        for deal in matched_deals:
            # Sort by the first matched keyword's index
            sort_key = min(keyword_map[kw] for kw in deal.matched_keywords) if deal.matched_keywords else -1
            deal.sort_key = sort_key
            
            log_message = "Deal found"
            if deal_history.is_new(deal.id):
                log_message = "New deal found"
                new_deals.append(deal)
            else:
                other_deals.append(deal)

            logger.info(
                log_message,
                id=deal.id,
                name=deal.title,
                price=deal.price,
                brand=deal.brand,
                matches=deal.matched_keywords,
                url=deal.url
            )

        new_deals.sort(key=lambda d: d.sort_key)
        other_deals.sort(key=lambda d: d.sort_key)
        
        # The final list of deals to be potentially emailed
        deals_for_email = new_deals + other_deals
        logger.info(f"Categorized {len(new_deals)} new deals and {len(other_deals)} other deals.")

        if send_email_flag:
            deals_to_email_not_sold_out = [deal for deal in deals_for_email if not deal.soldOut]
            logger.info(f"Found {len(deals_to_email_not_sold_out)} deals that are not sold out")

            if deals_to_email_not_sold_out:
                gmail_username = os.getenv("GMAIL_USERNAME")
                gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")
                gmail_recipient = os.getenv("GMAIL_RECIPIENT")

                if gmail_username and gmail_app_password and gmail_recipient:
                    logger.info("Generating HTML report and sending email...")
                    
                    new_deals_to_email = [d for d in new_deals if not d.soldOut]
                    other_deals_to_email = [d for d in other_deals if not d.soldOut]

                    html_report = generate_html_report(new_deals_to_email, other_deals_to_email)
                    send_email(html_report, gmail_username, gmail_recipient, gmail_app_password, len(deals_to_email_not_sold_out))
                else:
                    logger.warning("Email credentials not fully configured. Set GMAIL_USERNAME, GMAIL_APP_PASSWORD, and GMAIL_RECIPIENT environment variables.")
            else:
                logger.info("No deals to send in email.")

    except requests.RequestException as e:
        logger.error("HTTP request failed", error=str(e))
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON from response.")


def main():
    """
    Fetches all deals from the iBOOD API and prints them.
    """
    parser = argparse.ArgumentParser(description="Fetches iBOOD deals and optionally filters them by keywords.")
    parser.add_argument("--keywords", type=str, help="Path to a file containing keywords to filter deals (one keyword per line).")
    parser.add_argument("--send-email", action='store_true', help="Send the filtered deals in an HTML email.")
    parser.add_argument("--periodic", action='store_true', help="Run immediately and then every day at 2 AM.")
    args = parser.parse_args()

    keywords = []
    if args.keywords:
        try:
            with open(args.keywords, "r") as f:
                keywords = [line.strip() for line in f if line.strip()]
            logger.info("Loaded keywords", keywords=keywords)
        except FileNotFoundError:
            logger.error("Keywords file not found.", path=args.keywords)
            return

    if args.periodic:
        while True:
            # Run the job first, then wait for the next scheduled time
            fetch_and_process_deals(keywords, args.send_email)
            
            now = datetime.now()
            two_am_today = now.replace(hour=2, minute=0, second=0, microsecond=0)
            
            if now > two_am_today:
                # If it's already past 2 AM, schedule for 2 AM tomorrow
                next_run_base = two_am_today + timedelta(days=1)
            else:
                # Schedule for 2 AM today
                next_run_base = two_am_today

            # Add random delay
            random_minutes = random.randint(0, 5)
            random_seconds = random.randint(0, 60)
            delay = timedelta(minutes=random_minutes, seconds=random_seconds)
            next_run = next_run_base + delay

            # Ensure the next run time is in the future
            if next_run < now:
                next_run += timedelta(days=1)

            sleep_seconds = (next_run - now).total_seconds()
            
            logger.info(f"Next run scheduled at {next_run}, sleeping for {sleep_seconds:.0f} seconds.")
            time.sleep(sleep_seconds)
    else:
        fetch_and_process_deals(keywords, args.send_email)

if __name__ == "__main__":
    main()

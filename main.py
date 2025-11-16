from __future__ import print_function
from collections import namedtuple
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import os
import re
import smtplib
import sys
from typing import Generator, List, Optional, Tuple

import pandas as pd

from configs import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('secret_snowflake.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

Person = namedtuple('Person', ['name', 'email_address', 'mailing_address', 'gift_ideas'])

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def validate_email(email: str) -> bool:
    """
    Validate email address format

    Args:
        email: Email address to validate

    Returns:
        True if email format is valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    return EMAIL_REGEX.match(email.strip()) is not None


def validate_dataframe(df: pd.DataFrame) -> List[str]:
    """
    Validate DataFrame structure and contents

    Args:
        df: DataFrame to validate containing participant information

    Returns:
        List of validation error messages (empty list if valid)
    """
    errors = []

    # Check minimum number of participants
    if len(df) < 2:
        errors.append(f"Need at least 2 participants, found {len(df)}")

    # Check required columns exist
    required_columns = ['email_address', 'name', 'mailing_address', 'gift_ideas']
    for col in required_columns:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")

    if errors:
        return errors

    # Validate each row
    for idx, row in df.iterrows():
        # Check email format
        if not validate_email(row['email_address']):
            errors.append(f"Row {idx}: Invalid email address '{row['email_address']}'")

        # Check required fields are not empty
        if pd.isna(row['name']) or str(row['name']).strip() == '':
            errors.append(f"Row {idx}: Missing name for {row['email_address']}")

        if pd.isna(row['mailing_address']) or str(row['mailing_address']).strip() == '':
            errors.append(f"Row {idx}: Missing mailing address for {row['email_address']}")

        if pd.isna(row['gift_ideas']) or str(row['gift_ideas']).strip() == '':
            errors.append(f"Row {idx}: Missing gift ideas for {row['email_address']}")

    return errors

MSG_TXT = """
Happy Holidays {name}!

Joyce and I wish you a wonderful holiday season and a happy New Year!
Without further ado, please see your secret snowflake match below.

Your match is: {match_name}
Their email is: {match_email}
Their mailing address is: {match_mailing_address}
Their gift ideas: {match_gift_ideas}


https://github.com/k-schmidt/secret_snowflake
"""

MSG_HTML = """
<html>
  <body>
    <h2 style="color:DodgerBlue;"><i>Happy Holidays {name}!</i></h2>
    <p><i>Joyce and I hope you have a wonderful holiday season!<br>
    Without further ado, please see your secret snowflake match below.</i></p>

    <p>
    <i>Your match: {match_name} </i><br>
    <i>Their email: {match_email} </i><br>
    <i>Their mailing address: {match_mailing_address} </i><br>
    <i>Their gift ideas: {match_gift_ideas} </i><br>
    </p>

    <p style="font-size:70%;">https://github.com/k-schmidt/secret_snowflake</p>
"""

def send_email(giver: Person, receiver: Person) -> bool:
    """
    Generate and send email to giving person

    Args:
        giver: Person who will give the gift
        receiver: Person who will receive the gift

    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = Header(u"❄ Section D Secret Snowflake Match ❄", "utf-8")
        message["From"] = config.GMAIL_EMAIL
        message["To"] = giver.email_address
        part1 = MIMEText(
            MSG_TXT.format(
                name=giver.name,
                match_name=receiver.name,
                match_email=receiver.email_address,
                match_mailing_address=receiver.mailing_address,
                match_gift_ideas=receiver.gift_ideas,
            ),
            'plain'
        )
        part2 = MIMEText(
            MSG_HTML.format(
                name=giver.name,
                match_name=receiver.name,
                match_email=receiver.email_address,
                match_mailing_address=receiver.mailing_address,
                match_gift_ideas=receiver.gift_ideas,
            ),
            'html',
        )
        message.attach(part1)
        message.attach(part2)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(config.GMAIL_EMAIL, config.GMAIL_PW)
            server.sendmail(
                config.GMAIL_EMAIL, giver.email_address, message.as_string()
            )

        logging.info(f"✓ Email sent to {giver.name} ({giver.email_address})")
        return True

    except smtplib.SMTPAuthenticationError as e:
        logging.error(f"✗ SMTP Authentication failed: {e}")
        logging.error("Check your GMAIL_EMAIL and GMAIL_PW in .env file")
        return False
    except smtplib.SMTPException as e:
        logging.error(f"✗ Failed to send email to {giver.name} ({giver.email_address}): {e}")
        return False
    except Exception as e:
        logging.error(f"✗ Unexpected error sending email to {giver.name}: {e}")
        return False

def gen_matches(
    df: pd.DataFrame,
    max_attempts: int = 100,
    attempt: int = 0,
    random_seed: Optional[int] = None
) -> Generator[Tuple[Person, Person], None, None]:
    """
    Generate matches for each entered candidate

    Args:
        df: DataFrame of candidates
        max_attempts: Maximum number of retry attempts to prevent infinite recursion
        attempt: Current attempt number (used internally for recursion tracking)
        random_seed: Optional random seed for reproducible matching (useful for testing)
    """
    if attempt >= max_attempts:
        raise RuntimeError(
            f"Could not generate valid matches after {max_attempts} attempts. "
            "Check NO_MATCH_LIST constraints - they may make matching impossible."
        )

    # Build set of forbidden matches from NO_MATCH_LIST
    no_match_set = set(config.NO_MATCH_LIST)

    already_matched = set()
    all_emails = df['email_address'].tolist()

    for email in all_emails:
        # Find available match candidates
        available_matches = [
            m for m in all_emails
            if (m != email and
                (email, m) not in no_match_set and
                m not in already_matched)
        ]

        # Check if we have any valid matches available
        if not available_matches:
            # Deadlock detected - no valid matches left
            # Reset and try a different matching order
            yield from gen_matches(
                df.sample(frac=1, random_state=random_seed).reset_index(drop=True),
                max_attempts,
                attempt + 1,
                random_seed
            )
            return

        # Select a random match from available options
        match_df = df[df['email_address'].isin(available_matches)].sample(random_state=random_seed)
        match_email = match_df.iloc[0]['email_address']

        # Cache the lookup for the giving person to avoid repeated searches
        giving_person_df = df.loc[df['email_address'] == email]

        receiving_person = Person(
            name=match_df.iloc[0]['name'],
            email_address=match_df.iloc[0]['email_address'],
            mailing_address=match_df.iloc[0]['mailing_address'],
            gift_ideas=match_df.iloc[0]['gift_ideas'],
        )
        giving_person = Person(
            name=giving_person_df['name'].iloc[0],
            email_address=giving_person_df['email_address'].iloc[0],
            mailing_address=giving_person_df['mailing_address'].iloc[0],
            gift_ideas=giving_person_df['gift_ideas'].iloc[0],
        )
        already_matched.add(match_email)
        print(giving_person.name, receiving_person.name)

        yield (giving_person, receiving_person)

def main(responses_path: str) -> None:
    """
    Generates random matches from a csv file

    Args:
        responses_path: Path to input csv
    """
    logging.info("=" * 60)
    logging.info("Starting Secret Snowflake matching process")
    logging.info("=" * 60)

    # Validate environment variables
    if not config.GMAIL_EMAIL or not config.GMAIL_PW:
        logging.error("Missing Gmail credentials in .env file")
        logging.error("Please ensure GMAIL_EMAIL and GMAIL_PW are set in .env")
        sys.exit(1)

    # Check for optional random seed for reproducibility
    random_seed = None
    if os.getenv('RANDOM_SEED'):
        try:
            random_seed = int(os.getenv('RANDOM_SEED'))
            logging.info(f"Using random seed: {random_seed} (for reproducible matching)")
        except ValueError:
            logging.warning("RANDOM_SEED in .env is not a valid integer, ignoring")

    # Check if responses file exists
    try:
        logging.info(f"Reading participant data from: {responses_path}")
        df = pd.read_csv(
            responses_path,
            names=['timestamp', 'email_address', 'name', 'mailing_address', 'gift_ideas'],
            skiprows=1,
        )
    except FileNotFoundError:
        logging.error(f"File not found: {responses_path}")
        logging.error("Please ensure the CSV file exists at the specified path")
        sys.exit(1)
    except pd.errors.EmptyDataError:
        logging.error(f"File is empty: {responses_path}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
        sys.exit(1)

    # Remove duplicates
    original_count = len(df)
    df = df.drop_duplicates(subset='email_address', keep='first', ignore_index=True)
    if len(df) < original_count:
        duplicates_removed = original_count - len(df)
        logging.warning(f"Removed {duplicates_removed} duplicate email(s)")

    logging.info(f"Loaded {len(df)} participants")

    # Validate data
    validation_errors = validate_dataframe(df)
    if validation_errors:
        logging.error("Data validation failed:")
        for error in validation_errors:
            logging.error(f"  - {error}")
        sys.exit(1)

    logging.info("Data validation passed")

    # Generate matches
    try:
        logging.info("Generating matches...")
        matches = list(gen_matches(df, random_seed=random_seed))
        logging.info(f"Successfully generated {len(matches)} matches")
    except RuntimeError as e:
        logging.error(f"Failed to generate matches: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error during match generation: {e}")
        sys.exit(1)

    # Send emails and track results
    logging.info("Sending emails...")
    successful_emails = []
    failed_emails = []

    for giver, receiver in matches:
        success = send_email(giver, receiver)
        if success:
            successful_emails.append(giver.email_address)
        else:
            failed_emails.append(giver.email_address)

    # Summary
    logging.info("=" * 60)
    logging.info("Email sending complete")
    logging.info(f"Successfully sent: {len(successful_emails)}/{len(matches)}")
    if failed_emails:
        logging.warning(f"Failed to send: {len(failed_emails)}/{len(matches)}")
        logging.warning("Failed recipients:")
        for email in failed_emails:
            logging.warning(f"  - {email}")
    logging.info("=" * 60)


if __name__ == '__main__':
    main(config.PATH_RESPONSES)

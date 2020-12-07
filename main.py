from __future__ import print_function
from collections import namedtuple
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from typing import Generator, Tuple

import pandas as pd

from configs import config

Person = namedtuple('Person', ['name', 'email_address', 'mailing_address', 'gift_ideas'])

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
    <p><i>Joyce and I wish you a wonderful holiday season and a happy New Year!<br>
    Without further ado, please see your secret snowflake match below.</i></p>

    <p>
    <i>Your match: {match_name} </i><br>
    <i>Their email: {match_email} </i><br>
    <i>Their mailing address: {match_mailing_address} </i><br>
    <i>Their gift ideas: {match_gift_ideas} </i><br>
    </p>

    <p style="font-size:70%;">https://github.com/k-schmidt/secret_snowflake</p>
"""

def send_email(giver: Person, receiver: Person) -> None:
    """
    Generate email to send to giving person

    giver: Person to give gift
    receiver: Person to receive gift
    """
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
    with smtplib.SMTP_SSL("smtp.gmail.com") as server:
        server.login(config.GMAIL_EMAIL, config.GMAIL_PW)
        server.sendmail(
            config.GMAIL_EMAIL, config.GMAIL_EMAIL, message.as_string()
        )

def gen_matches(df: pd.DataFrame) -> Generator[Tuple[Person, Person], None, None]:
    """
    Generate matches for each entered candidate

    df: DataFrame of candidates
    """
    already_matched = set()
    for email in df['email_address']:
        match_email = None
        while (
            match_email is None
            or email == match_email
            or match_email == config.NO_MATCH_DICT.get(email)
            or match_email in already_matched
        ):
            df_match = df.sample()
            match_email = df_match.iloc[0]['email_address']

        receiving_person = Person(
            name=df_match.iloc[0]['name'],
            email_address=df_match.iloc[0]['email_address'],
            mailing_address=df_match.iloc[0]['mailing_address'],
            gift_ideas=df_match.iloc[0]['gift_ideas'],
        )
        giving_person = Person(
            name=df.loc[df['email_address'] == email]['name'].iloc[0],
            email_address=df.loc[df['email_address'] == email]['email_address'].iloc[0],
            mailing_address=df.loc[df['email_address'] == email]['mailing_address'].iloc[0],
            gift_ideas=df.loc[df['email_address'] == email]['gift_ideas'].iloc[0],
        )
        already_matched.add(match_email)

        yield (giving_person, receiving_person)

def main(responses_path: str) -> None:
    """
    Generates random matches from a tsv file

    responses_path: Path to input tsv

    """
    df = pd.read_csv(
        responses_path,
        sep='\t',
        names=['timestamp', 'email_address', 'name', 'mailing_address', 'gift_ideas',],
        skiprows=1,
    )
    df = df.drop_duplicates(subset='email_address', keep='first', ignore_index=True)
    matches = gen_matches(df)
    for giver, receiver in matches:
        send_email(giver, receiver)


if __name__ == '__main__':
    main(config.PATH_RESPONSES)

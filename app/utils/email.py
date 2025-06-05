import os
from os import access

import boto3
from botocore.exceptions import ClientError

def send_abonnement_email(to_email, voornaam, abonnement_type, einddatum):
    if not to_email:
        print("❌ Geen geldig e-mailadres opgegeven. E-mail niet verzonden.")
        return

    ses = boto3.client('ses', region_name='eu-west-1',aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))  # pas regio aan indien nodig

    subject = "Bevestiging van je abonnement"
    body_text = f"""
    Beste {voornaam},

    Bedankt voor je aankoop van een {abonnement_type}-abonnement.
    Je abonnement is geldig tot: {einddatum}.

    Veel plezier met onze dienst!

    Met vriendelijke groet,  
    Het Grandpabob Team
    """

    try:
        response = ses.send_email(
            Source="noreply@grandpabob.net",  # <- Verified domain
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Text": {"Data": body_text, "Charset": "UTF-8"}
                    # Je kan hier ook 'Html' toevoegen als je HTML-mails wilt
                },
            },
        )
        print(f"✅ E-mail verzonden: {response['MessageId']}")
        return response['MessageId']

    except ClientError as e:
        print(f"❌ Fout bij verzenden e-mail: {e.response['Error']['Message']}")
        return None

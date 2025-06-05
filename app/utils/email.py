import os
from os import access
import boto3
from botocore.exceptions import ClientError

#Functie voor een bevesitingsmail bij successvolle betaling.
def send_abonnement_email(to_email, voornaam, abonnement_type, einddatum):
    # controleren of er een e-mailadres is opgegeven.
    if not to_email:
        print("❌ Geen geldig e-mailadres opgegeven. E-mail niet verzonden.")
        return
    #simple service client (inloggen en connecteren met aws systeem)
    ses = boto3.client('ses', region_name='eu-west-1',aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
    #onderwerp en tekts in de email declareren
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
        # verstuur de e-mail via de ses client
        response = ses.send_email(
            Source="noreply@grandpabob.net",  # de domeinnaam in aws hier zetten
            Destination={"ToAddresses": [to_email]}, #ontvanger
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"}, #onderwerp
                "Body": { #inhoud
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

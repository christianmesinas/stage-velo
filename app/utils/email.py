import boto3
from botocore.exceptions import ClientError
import os

def send_abonnement_email(to_email, voornaam, abonnement_type, einddatum):
    ses = boto3.client('ses', region_name='eu-west-1', aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"), aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"))
    subject = "Bevestiging van je abonnement"
    body = f"""
    Beste {voornaam},
    
    Bedankt voor je aankoop van een {abonnement_type}-abonnement.
    Je abonnement is geldig tot: {einddatum}. 
    
    Veel plezier met onze dienst! 
    
    Met vriendelijke groet,
    Het Velo Team
    """

    try:
        response = ses.send_email(
            Source="komutsalih@gmail.com",
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": body}},
            }
        )
        return response["MessageId"]
    except ClientError as e:
        print(f"Fout bij het verzenden e-mail: {e}")
        return None
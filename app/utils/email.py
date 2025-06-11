import os
import smtplib
from email.mime.text import MIMEText

def send_abonnement_email(to_email, voornaam, abonnement_type, einddatum):
    if not to_email:
        print("❌ Geen geldig e-mailadres opgegeven. E-mail niet verzonden.")
        return

    # Gmail SMTP-configuratie (gebruik omgevingsvariabelen voor veiligheid)
    GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")         # jouw Gmail-adres
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")  # App-wachtwoord van Gmail

    if not GMAIL_EMAIL or not GMAIL_APP_PASSWORD:
        print("❌ Gmail-gegevens ontbreken. Controleer je omgevingsvariabelen.")
        return

    # Mailinhoud
    subject = "Bevestiging van je abonnement"
    body_text = f"""
    Beste {voornaam},

    Bedankt voor je aankoop van een {abonnement_type}-abonnement.
    Je abonnement is geldig tot: {einddatum}.

    Veel plezier met onze dienst!

    Met vriendelijke groet,  
    Het Grandpabob Team
    """

    # Opmaak van de e-mail
    msg = MIMEText(body_text)
    msg['Subject'] = subject
    msg['From'] = f"Grandpabob <{GMAIL_EMAIL}>"
    msg['To'] = to_email

    try:
        # Verbind met Gmail SMTP-server
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
            server.send_message(msg)
            print(f"✅ E-mail succesvol verzonden naar {to_email}")
            return True

    except smtplib.SMTPException as e:
        print(f"❌ SMTP-fout bij verzenden: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Onverwachte fout: {str(e)}")
        return False
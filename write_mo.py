from babel.messages.pofile import read_po
from babel.messages.mofile import write_mo
import io

# Load your Spanish .po file
with open("app/translations/es/LC_MESSAGES/messages.po", "r", encoding="utf-8") as f:
    po_file = io.StringIO(f.read())

# Parse the PO file
catalog = read_po(po_file)

# Check if catalog is valid
print(f"Total messages: {len(catalog)}")
for message in catalog:
    if message.id and not message.string:
        print(f"⚠️ Missing translation for: {message.id}")

# Compile to .mo file
with open("app/translations/es/LC_MESSAGES/messages.mo", "wb") as f:
    write_mo(f, catalog)

print("✅ Spanish translation file compiled successfully.")

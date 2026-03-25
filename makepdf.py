import io
import os
import random
from reportlab.pdfgen import canvas

def genereer_exacte_pdf(bestandsnaam, doel_bytes):
    # Stap 1: Maak de PDF eerst aan in het werkgeheugen
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    
    # Stap 2: Voeg de random gekleurde bits toe
    # We tekenen 20 blokjes. Dit houdt het basisbestand klein (~2KB),
    # zodat we bij het 5KB bestand niet direct over het doel heen schieten.
    for _ in range(20):
        r, g, b = random.random(), random.random(), random.random()
        c.setFillColorRGB(r, g, b)
        
        # Willekeurige positie op de pagina
        x = random.randint(0, 500)
        y = random.randint(0, 800)
        c.rect(x, y, 20, 20, fill=1, stroke=0)
        
    c.save()
    pdf_data = buffer.getvalue()
    huidige_grootte = len(pdf_data)
    
    # Stap 3: Controleer de grootte en pas exact aan (zonder loops!)
    if huidige_grootte == doel_bytes:
        eind_data = pdf_data
        
    elif huidige_grootte < doel_bytes:
        # Bestand is te klein. We rekenen het tekort uit en vullen dit op.
        # In een PDF wordt alles na een '%' gezien als commentaar.
        tekort = doel_bytes - huidige_grootte
        if tekort >= 2:
            # We voegen een newline en '%' toe, gevuld met willekeurige bytes
            padding = b'\n%' + os.urandom(tekort - 2)
        else:
            padding = b' ' * tekort
        eind_data = pdf_data + padding
        
    else:
        # Fallback: Mocht het basisbestand tóch groter zijn dan het doel (overshoot),
        # dan maken we een ultiem kale PDF om loops te voorkomen en vullen we die op.
        buffer_fallback = io.BytesIO()
        c_fallback = canvas.Canvas(buffer_fallback)
        c_fallback.drawString(100, 400, "Fallback voor exacte grootte")
        c_fallback.save()
        pdf_data = buffer_fallback.getvalue()
        
        tekort = doel_bytes - len(pdf_data)
        padding = b'\n%' + os.urandom(max(0, tekort - 2)) if tekort >= 2 else b' ' * tekort
        eind_data = pdf_data + padding

    # Stap 4: Sla het uiteindelijke bestand op je harde schijf op
    with open(bestandsnaam, 'wb') as f:
        f.write(eind_data)
        
    print(f"Opgeslagen: {bestandsnaam.ljust(15)} | Doel: {doel_bytes} bytes | Resultaat: {len(eind_data)} bytes")

# --- Uitvoering ---
print("Genereren gestart...")

# Exacte bytes: 5KB, 50KB en 5000KB (5MB)
genereer_exacte_pdf('test_5KB.pdf', 5120)
genereer_exacte_pdf('test_50KB.pdf', 51200)
genereer_exacte_pdf('test_5000KB.pdf', 5120000)

print("Klaar! Je bestanden staan in dezelfde map als dit script.")
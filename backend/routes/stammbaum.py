from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from db import get_pg_connection, release_pg_connection

router = APIRouter()

async def get_person_recursive(conn, person_id, depth):
    if not person_id or depth < 0:
        return None
    
    row = await conn.fetchrow("SELECT id, vorname, nachname, geburtsdatum, vater_id, mutter_id FROM personen WHERE id = $1", person_id)
    if not row:
        return None
    
    p = dict(row)
    if depth > 0:
        p["vater"] = await get_person_recursive(conn, p["vater_id"], depth - 1)
        p["mutter"] = await get_person_recursive(conn, p["mutter_id"], depth - 1)
    return p

def draw_tree(c, person, x, y, width, height, level):
    if not person:
        return

    # Box zeichnen
    box_w = 4.5 * cm
    box_h = 1.2 * cm
    c.rect(x - box_w/2, y - box_h/2, box_w, box_h)
    
    # Text in Box
    name = f"{person['vorname']} {person['nachname']}"
    datum = f"* {person['geburtsdatum'].strftime('%d.%m.%Y')}" if person.get('geburtsdatum') else ""
    
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(x, y + 0.1*cm, name[:25])
    c.setFont("Helvetica", 8)
    c.drawCentredString(x, y - 0.3*cm, datum)

    # Eltern zeichnen (Rekursion)
    if "vater" in person or "mutter" in person:
        new_width = width / 2
        v_y = y + 3.5 * cm # Abstand nach oben zur nächsten Generation
        
        # Verbindungslinien
        if person.get("vater") or person.get("mutter"):
            c.line(x, y + box_h/2, x, y + 1.5 * cm) # Vertikal nach oben
            c.line(x - new_width, y + 1.5 * cm, x + new_width, y + 1.5 * cm) # Horizontal
            c.line(x - new_width, y + 1.5 * cm, x - new_width, v_y - box_h/2) # Zu Vater
            c.line(x + new_width, y + 1.5 * cm, x + new_width, v_y - box_h/2) # Zu Mutter

        draw_tree(c, person.get("vater"), x - new_width, v_y, new_width, height, level + 1)
        draw_tree(c, person.get("mutter"), x + new_width, v_y, new_width, height, level + 1)

@router.get("/{person_id}/pdf/")
async def generate_stammbaum_pdf(person_id: int, gen: int = 3):
    conn = await get_pg_connection()
    try:
        # 1. Daten laden
        person_data = await get_person_recursive(conn, person_id, gen)
        if not person_data:
            raise HTTPException(status_code=404, detail="Person nicht gefunden")

        # 2. PDF erstellen
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=landscape(A4))
        page_w, page_h = landscape(A4)

        # Titel
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(page_w/2, page_h - 2*cm, f"Stammbaum: {person_data['vorname']} {person_data['nachname']}")
        
        # Baum zeichnen (Startpunkt unten Mitte, geht nach oben)
        draw_tree(c, person_data, page_w/2, 4*cm, page_w/3, page_h, 0)

        c.showPage()
        c.save()
        
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=stammbaum_{person_id}.pdf"}
        )

    finally:
        await release_pg_connection(conn)
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import date
from db import get_pg_connection, release_pg_connection

router = APIRouter()

# --- Schemas ---
class PersonBase(BaseModel):
    vorname: str
    nachname: str
    geburtsdatum: Optional[date] = None
    geschlecht: Optional[bool] = None  # True = Männlich, False = Weiblich
    vater_id: Optional[int] = None
    mutter_id: Optional[int] = None

    @field_validator('vater_id', 'mutter_id', mode='before')
    @classmethod
    def zero_to_none(cls, v):
        if v == 0 or v == "":
            return None
        return v

class PersonCreate(PersonBase):
    pass

class PersonUpdate(BaseModel):
    vorname: Optional[str] = None
    nachname: Optional[str] = None
    geburtsdatum: Optional[date] = None
    geschlecht: Optional[bool] = None
    vater_id: Optional[int] = None
    mutter_id: Optional[int] = None

    @field_validator('vater_id', 'mutter_id', mode='before')
    @classmethod
    def zero_to_none(cls, v):
        if v == 0 or v == "":
            return None
        return v

class PersonOut(PersonBase):
    id: int

# --- CRUD Endpunkte ---



@router.get("/search/", response_model=List[PersonOut])
async def search_personen(q: str):
    conn = await get_pg_connection()
    try:
        # Suche in Vorname oder Nachname (case-insensitive)
        rows = await conn.fetch('''
            SELECT * FROM personen 
            WHERE vorname ILIKE $1 OR nachname ILIKE $1 
            ORDER BY nachname, vorname
            LIMIT 15
        ''', f'%{q}%')
        return [dict(r) for r in rows]
    finally:
        await release_pg_connection(conn)

# 2. STECKBRIEF (Umfassende Daten für die UI)
@router.get("/{person_id}/steckbrief/")
async def get_person_steckbrief(person_id: int):
    conn = await get_pg_connection()
    try:
        # Grunddaten
        person_row = await conn.fetchrow('SELECT * FROM personen WHERE id = $1', person_id)
        if not person_row:
            raise HTTPException(status_code=404, detail="Person nicht gefunden")
        
        p = dict(person_row)
        
        # Eltern laden
        vater = await conn.fetchrow('SELECT id, vorname, nachname FROM personen WHERE id = $1', p['vater_id']) if p['vater_id'] else None
        mutter = await conn.fetchrow('SELECT id, vorname, nachname FROM personen WHERE id = $1', p['mutter_id']) if p['mutter_id'] else None
        
        # Geschwister laden
        # Logik: Gleiche Eltern, aber nicht die Person selbst
        geschwister = await conn.fetch('''
            SELECT id, vorname, nachname, geburtsdatum FROM personen 
            WHERE (vater_id = $1 OR mutter_id = $2) 
            AND id != $3
            ORDER BY geburtsdatum ASC
        ''', p['vater_id'], p['mutter_id'], person_id)

        # Kinder laden
        kinder = await conn.fetch('''
            SELECT id, vorname, nachname, geburtsdatum FROM personen 
            WHERE vater_id = $1 OR mutter_id = $1
            ORDER BY geburtsdatum ASC
        ''', person_id)

        return {
            "person": p,
            "eltern": {
                "vater": dict(vater) if vater else None, 
                "mutter": dict(mutter) if mutter else None
            },
            "geschwister": [dict(r) for r in geschwister],
            "kinder": [dict(r) for r in kinder]
        }
    finally:
        await release_pg_connection(conn)


    
@router.get("/", response_model=List[PersonOut])
async def get_all_personen():
    conn = await get_pg_connection()
    try:
        rows = await conn.fetch('SELECT * FROM personen ORDER BY nachname, vorname')
        return [dict(r) for r in rows]
    finally:
        await release_pg_connection(conn)

@router.get("/{person_id}/", response_model=PersonOut)
async def get_person(person_id: int):
    conn = await get_pg_connection()
    try:
        row = await conn.fetchrow('SELECT * FROM personen WHERE id = $1', person_id)
        if not row:
            raise HTTPException(status_code=404, detail="Person nicht gefunden")
        return dict(row)
    finally:
        await release_pg_connection(conn)

@router.post("/", response_model=PersonOut)
async def create_person(data: PersonCreate):
    conn = await get_pg_connection()
    try:
        # Wir fügen die Basidaten ein. 
        # Falls Felder im Schema optional sind, werden sie als NULL gespeichert.
        row = await conn.fetchrow('''
            INSERT INTO personen (vorname, nachname, geburtsdatum, geschlecht, vater_id, mutter_id)
            VALUES ($1, $2, $3, $4, $5, $6) 
            RETURNING id, vorname, nachname, geburtsdatum, geschlecht, vater_id, mutter_id
        ''', data.vorname, data.nachname, data.geburtsdatum, data.geschlecht, data.vater_id, data.mutter_id)
        
        return dict(row)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Datenbankfehler: {str(e)}")
    finally:
        await release_pg_connection(conn)


@router.put("/{person_id}/", response_model=PersonOut)
async def update_person(person_id: int, data: PersonUpdate):
    conn = await get_pg_connection()
    try:
        fields = data.model_dump(exclude_unset=True)
        if not fields:
            raise HTTPException(status_code=400, detail="Keine Daten zum Update geliefert")
        
        set_query = ", ".join([f"{key} = ${i+2}" for i, key in enumerate(fields.keys())])
        values = list(fields.values())
        
        sql = f"UPDATE personen SET {set_query} WHERE id = $1 RETURNING *"
        row = await conn.fetchrow(sql, person_id, *values)
        if not row:
            raise HTTPException(status_code=404, detail="Person nicht gefunden")
        return dict(row)
    finally:
        await release_pg_connection(conn)

@router.delete("/{person_id}/")
async def delete_person(person_id: int):
    conn = await get_pg_connection()
    try:
        status = await conn.execute('DELETE FROM personen WHERE id = $1', person_id)
        if status == "DELETE 0":
            raise HTTPException(status_code=404, detail="Person nicht gefunden")
        return {"status": "success", "id": person_id}
    finally:
        await release_pg_connection(conn)

# --- Rekursiver Stammbaum ---

async def fetch_person_recursive(conn, person_id: int, max_depth: int, current_depth: int = 0):
    if current_depth > max_depth or person_id is None:
        return None
    
    row = await conn.fetchrow("SELECT * FROM personen WHERE id = $1", person_id)
    if not row:
        return None
    
    person_dict = dict(row)
    
    # Rekursiv Vater und Mutter laden
    if current_depth < max_depth:
        person_dict["vater"] = await fetch_person_recursive(conn, person_dict["vater_id"], max_depth, current_depth + 1)
        person_dict["mutter"] = await fetch_person_recursive(conn, person_dict["mutter_id"], max_depth, current_depth + 1)
    
    return person_dict

@router.get("/{person_id}/stammbaum-json/")
async def get_stammbaum_recursive(person_id: int, tiefe: int = 3):
    conn = await get_pg_connection()
    try:
        result = await fetch_person_recursive(conn, person_id, tiefe)
        if not result:
            raise HTTPException(status_code=404, detail="Person nicht gefunden")
        return result
    finally:
        await release_pg_connection(conn)

        
# -*- coding: utf-8 -*-
"""
seed_data.py — Réinitialisation & peuplement de la BD ngokaf_trans
Usage : python scripts/seed_data.py
"""
from __future__ import annotations

import sys
import io

# Forcer l'encodage UTF-8 pour la console Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import os
import random
import json
from datetime import date, datetime, time, timedelta
from decimal import Decimal

# Ajouter la racine du projet au chemin
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database.connection import init_connection
from database.session import Base, get_session
from database.migrate import migrate_schema, migrate_nullable
import bcrypt

import models  # noqa : enregistre tous les modèles ORM
from models import (
    User, Bus, Seat, Driver, Route, Ticket, TicketCancellation,
    Luggage, Expense, Notification, Sequence, AppSetting,
)

# ────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """bcrypt hash — identique à auth_service.py."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def rand_phone() -> str:
    prefixes = ["6 70", "6 75", "6 80", "6 85", "6 90", "6 91", "6 93", "6 94", "6 55", "6 50"]
    return f"+237 {random.choice(prefixes)} {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99)}"


def rand_date_in_range(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def make_qr(ticket_no: str, passenger: str, route: str, travel_date: date) -> str:
    return json.dumps({
        "ticket": ticket_no,
        "passenger": passenger,
        "route": route,
        "date": travel_date.isoformat(),
        "agency": "NGOKAF TRANS",
    })


# ────────────────────────────────────────────────────
# Données de référence
# ────────────────────────────────────────────────────

VILLES = [
    ("Douala",    "Yaoundé",    "06:00", "09:30", 240,  5500),
    ("Douala",    "Bafoussam",  "07:00", "11:00", 300,  4500),
    ("Douala",    "Buea",       "08:00", "10:00", 70,   2500),
    ("Yaoundé",   "Bafoussam",  "07:30", "11:30", 280,  4000),
    ("Yaoundé",   "Ngaoundéré", "08:00", "15:00", 600,  8000),
    ("Douala",    "Kribi",      "09:00", "12:00", 140,  3500),
    ("Bafoussam", "Bamenda",    "08:00", "10:30", 100,  2500),
    ("Douala",    "Limbe",      "07:00", "08:30", 30,   1500),
]

PRENOMS = ["Jean", "Marie", "Paul", "Sophie", "Alain", "Claire", "Joseph", "Isabelle",
           "Pierre", "Fatima", "Moussa", "Aminata", "Patrick", "Rose", "Emmanuel",
           "Sandrine", "Victor", "Christelle", "Daniel", "Flore", "Roger", "Henriette"]

NOMS    = ["Mballa", "Nkeng", "Fopa", "Biya", "Etoa", "Ngono", "Talla", "Kpan",
           "Fouda", "Ayuk", "Ndongo", "Belinga", "Tchamba", "Moukam", "Essomba",
           "Atangana", "Djiomou", "Kamga", "Bilong", "Nguele", "Nganou", "Wamba"]

BUS_DATA = [
    ("BUS-001", "LT-1234-A", "Mercedes", "Tourismo",    2020, "Blanc",  70, "2-2"),
    ("BUS-002", "LT-5678-B", "Yutong",   "ZK6122H9",   2019, "Bleu",   60, "2-2"),
    ("BUS-003", "LT-9012-C", "Toyota",   "Coaster",     2021, "Blanc",  30, "2-2"),
    ("BUS-004", "LT-3456-D", "King Long","XMQ6127Y",   2018, "Jaune",  60, "2-2"),
    ("BUS-005", "LT-7890-E", "Higer",    "KLQ6125",     2022, "Blanc",  55, "2-2"),
]


# ────────────────────────────────────────────────────
# Réinitialisation
# ────────────────────────────────────────────────────

def drop_and_recreate(engine) -> None:
    print("🗑️  Suppression des tables existantes…")
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for table in [
            "ticket_cancellations", "tickets", "luggage",
            "routes", "seats", "drivers", "buses",
            "expenses", "audit_logs", "login_logs",
            "notifications", "sequences", "app_settings", "users",
        ]:
            conn.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    print("✅  Tables supprimées.")

    print("🏗️  Création des tables via SQLAlchemy…")
    Base.metadata.create_all(bind=engine)
    migrate_schema(engine)
    migrate_nullable(engine)
    print("✅  Tables créées.")


# ────────────────────────────────────────────────────
# Peuplement
# ────────────────────────────────────────────────────

def seed(session) -> None:

    # ── 1. Paramètres application ───────────────────
    print("⚙️  Paramètres par défaut…")
    defaults = {
        "agency_name":             "NGOKAF TRANS",
        "agency_address":          "BP 1245 - Douala, Cameroun",
        "agency_phone":            "+237 6 99 11 22 33",
        "terminal_name":           "TERMINAL PRINCIPAL",
        "luggage_base_fee":        "2500",
        "luggage_weight_rate":     "200",
        "session_timeout_minutes": "30",
        "ticket_prefix":           "TKT",
        "currency":                "FCFA",
    }
    for k, v in defaults.items():
        session.add(AppSetting(key=k, value=v))
    session.flush()

    # ── 2. Séquences ───────────────────────────────
    print("🔢  Séquences…")
    for sname in ["ticket", "luggage"]:
        session.add(Sequence(name=sname, seq_date=date.today(), value=0))
    session.flush()

    # ── 3. Utilisateurs ────────────────────────────
    print("👥  Utilisateurs…")
    admin = User(
        nom="Admin", prenom="Super",
        username="admin",
        password_hash=hash_password("B@nheur2026!"),
        role="administrateur", statut="actif",
        telephone=rand_phone(),
        email="admin@ngokaf-trans.cm",
        adresse="Akwa, Douala",
        created_at=datetime(2026, 1, 1, 8, 0),
    )
    session.add(admin)

    caissiers = []
    caissier_infos = [
        ("Mballa",   "Jean",     "caissier1", "Bonanjo, Douala"),
        ("Nkeng",    "Marie",    "caissier2", "Makepe, Douala"),
        ("Fopa",     "Alain",    "caissier3", "Bastos, Yaoundé"),
        ("Talla",    "Sandrine", "caissier4", "Bafoussam"),
    ]
    for nom, prenom, uname, adresse in caissier_infos:
        u = User(
            nom=nom, prenom=prenom,
            username=uname,
            password_hash=hash_password("Caissier@2026!"),
            role="caissier", statut="actif",
            telephone=rand_phone(),
            email=f"{uname}@ngokaf-trans.cm",
            adresse=adresse,
            created_at=datetime(2026, 1, 15, 8, 0),
        )
        session.add(u)
        caissiers.append(u)
    session.flush()

    # ── 4. Bus ─────────────────────────────────────
    print("🚌  Bus…")
    buses = []
    for code, plaque, marque, modele, annee, couleur, capacite, layout in BUS_DATA:
        b = Bus(
            code=code, plaque=plaque, marque=marque,
            modele=modele, annee=annee, couleur=couleur,
            capacite=capacite, layout=layout,
            statut="actif",
            date_achat=date(annee, random.randint(1, 12), random.randint(1, 28)),
            created_at=datetime(2026, 1, 5, 9, 0),
        )
        session.add(b)
        buses.append(b)
    session.flush()

    # Sièges pour chaque bus
    print("💺  Sièges…")
    for bus in buses:
        for num in range(1, bus.capacite + 1):
            session.add(Seat(bus_id=bus.id, numero=num))
    session.flush()

    # ── 5. Chauffeurs ──────────────────────────────
    print("🧑  Chauffeurs…")
    drivers_data = [
        ("Nguele", "Robert",   "+237 6 71 23 45 67", "DLA-001-2021", date(2028, 6, 30)),
        ("Kamga",  "Bertrand", "+237 6 72 34 56 78", "DLA-002-2020", date(2027, 3, 15)),
        ("Bilong", "Clément",  "+237 6 73 45 67 89", "YAO-003-2022", date(2029, 1, 20)),
        ("Wamba",  "Serge",    "+237 6 74 56 78 90", "BFS-004-2019", date(2026, 12, 31)),
        ("Nganou", "Achille",  "+237 6 75 67 89 01", "DLA-005-2023", date(2030, 5, 10)),
    ]
    drivers = []
    for i, (nom, prenom, tel, permis, exp) in enumerate(drivers_data):
        d = Driver(
            nom=nom, prenom=prenom, telephone=tel,
            numero_permis=permis,
            date_expiration_permis=exp,
            bus_id=buses[i].id,
            statut="actif",
            disponibilite="disponible",
            adresse=f"Quartier {random.choice(['Akwa','Bonanjo','Bepanda','Makepe'])}, Douala",
            created_at=datetime(2026, 1, 10, 8, 0),
        )
        session.add(d)
        drivers.append(d)
    session.flush()

    # ── 6. Routes ──────────────────────────────────
    print("🗺️  Routes…")
    routes = []
    for i, (vd, va, hd, ha, dist, prix) in enumerate(VILLES):
        r = Route(
            ville_depart=vd, ville_arrivee=va,
            heure_depart=time(*[int(x) for x in hd.split(":")]),
            heure_arrivee=time(*[int(x) for x in ha.split(":")]),
            distance_km=Decimal(str(dist)),
            prix_indicatif=Decimal(str(prix)),
            bus_id=buses[i % len(buses)].id,
            driver_id=drivers[i % len(drivers)].id,
            statut="actif",
            created_at=datetime(2026, 2, 1, 8, 0),
        )
        session.add(r)
        routes.append(r)
    session.flush()

    # ── 7. Tickets ─────────────────────────────────
    print("🎫  Tickets (200 billets)…")
    start_date = date(2026, 6, 1)
    end_date   = date(2026, 8, 29)
    ticket_counter = 1
    tickets_created = []

    for _ in range(200):
        route   = random.choice(routes)
        cashier = random.choice(caissiers)
        vente   = rand_date_in_range(start_date, end_date)
        travel  = vente + timedelta(days=random.randint(0, 3))
        seat_no = random.randint(1, route.bus.capacite)
        prenom  = random.choice(PRENOMS)
        nom     = random.choice(NOMS)
        passenger = f"{prenom} {nom}"
        numero  = f"TKT-{vente.strftime('%Y%m%d')}-{ticket_counter:04d}"
        ticket_counter += 1

        t = Ticket(
            numero=numero,
            date_vente=vente,
            passenger_name=passenger,
            phone=rand_phone(),
            route_id=route.id,
            bus_id=route.bus_id,
            seat_number=seat_no,
            price=route.prix_indicatif or Decimal("5000"),
            travel_date=travel,
            qr_payload=make_qr(numero, passenger, route.short_label, travel),
            cashier_id=cashier.id,
            statut=random.choices(
                ["vendu", "utilisé", "annulé"],
                weights=[60, 30, 10]
            )[0],
            created_at=datetime(vente.year, vente.month, vente.day,
                                random.randint(6, 18), random.randint(0, 59)),
        )
        session.add(t)
        tickets_created.append(t)
    session.flush()

    # Annulations
    cancelled = [t for t in tickets_created if t.statut == "annulé"]
    reasons = [
        "Problème familial", "Voyage reporté", "Erreur de réservation",
        "Client absent", "Maladie", "Urgence professionnelle",
    ]
    for t in cancelled:
        session.add(TicketCancellation(
            ticket_id=t.id,
            reason=random.choice(reasons),
            cancelled_by=admin.id,
            cancelled_at=datetime(t.date_vente.year, t.date_vente.month,
                                  t.date_vente.day, 14, 0),
        ))
    session.flush()

    # ── 8. Bagages ─────────────────────────────────
    print("🧳  Bagages (80 colis)…")
    baggage_counter = 1
    for _ in range(80):
        route     = random.choice(routes)
        cashier   = random.choice(caissiers)
        dep_day   = rand_date_in_range(start_date, end_date)
        created_dt = datetime(dep_day.year, dep_day.month, dep_day.day,
                              random.randint(6, 17), random.randint(0, 59))
        poids      = Decimal(str(round(random.uniform(2.0, 50.0), 1)))
        frais_base = Decimal("2500")
        supplement = max(Decimal("0"), (poids - Decimal("5")) * Decimal("200"))
        total      = frais_base + supplement
        num        = f"BAG-{dep_day.strftime('%Y%m%d')}-{baggage_counter:04d}"
        baggage_counter += 1

        session.add(Luggage(
            numero=num,
            sender_name=f"{random.choice(PRENOMS)} {random.choice(NOMS)}",
            sender_phone=rand_phone(),
            recipient_name=f"{random.choice(PRENOMS)} {random.choice(NOMS)}",
            recipient_phone=rand_phone(),
            description=random.choice([
                "Vêtements et effets personnels",
                "Provisions alimentaires",
                "Matériel électronique",
                "Livres et documents",
                "Pièces détachées moto",
                "Produits cosmétiques",
                "Colis médical",
                "Mobilier léger",
            ]),
            poids=poids,
            valeur_declaree=Decimal(str(random.randint(5000, 500000))),
            route_id=route.id,
            bus_id=route.bus_id,
            frais_base=frais_base,
            supplement_poids=supplement,
            total=total,
            barcode=f"NGK{num.replace('-', '')}",
            qr_payload=json.dumps({"bagage": num, "agence": "NGOKAF TRANS"}),
            cashier_id=cashier.id,
            statut=random.choices(
                ["enregistre", "en_transit", "livre"],
                weights=[30, 30, 40]
            )[0],
            fragile=random.random() < 0.2,
            created_at=created_dt,
        ))
    session.flush()

    # ── 9. Dépenses ────────────────────────────────
    print("💰  Dépenses (60 entrées)…")
    depenses_templates = [
        ("carburant",            "Gasoil pour bus {bus}",           8000,  150000, "especes"),
        ("entretien_bus",        "Révision périodique bus {bus}",   50000, 300000, "especes"),
        ("salaires",             "Salaire chauffeur {mois}",        80000, 200000, "virement"),
        ("frais_administratifs", "Frais de bureau {mois}",           5000,  30000, "especes"),
        ("assurance",            "Assurance flotte {mois}",         30000, 120000, "virement"),
        ("location",             "Loyer terminal {mois}",           50000, 100000, "virement"),
        ("autres",               "Dépenses diverses {mois}",         2000,  20000, "especes"),
        ("entretien_bus",        "Pneus neufs bus {bus}",           80000, 200000, "cheque"),
        ("carburant",            "Gasoil trajet {mois}",             5000,  50000, "especes"),
        ("assurance",            "Visite technique {bus}",          10000,  25000, "especes"),
    ]
    mois_labels = ["Juin 2026", "Juillet 2026", "Août 2026"]

    for _ in range(60):
        cat, desc_tpl, mn, mx, mode = random.choice(depenses_templates)
        dep_date   = rand_date_in_range(date(2026, 6, 1), date(2026, 8, 29))
        bus_label  = random.choice([b.code for b in buses])
        mois_label = random.choice(mois_labels)
        session.add(Expense(
            date_paiement=dep_date,
            categorie=cat,
            montant=Decimal(str(random.randint(mn // 1000, mx // 1000) * 1000)),
            description=desc_tpl.format(bus=bus_label, mois=mois_label),
            mode_paiement=mode,
            fournisseur=random.choice([
                "Total Energies Douala", "Carrefour Auto", "Camtel",
                "CNPS", "Société Générale", "Afriland First Bank",
                "Garage Central Douala", None,
            ]),
            created_by=admin.id,
            created_at=datetime(dep_date.year, dep_date.month, dep_date.day,
                                random.randint(8, 17), random.randint(0, 59)),
        ))
    session.flush()

    # ── 10. Notifications ──────────────────────────
    print("🔔  Notifications…")
    notifs = [
        ("Bienvenue",             "Système initialisé avec succès !",                    "info",    "bell"),
        ("Stock bas",             "Bus BUS-004 : révision dans 500 km.",                 "warning", "wrench"),
        ("Nouveau trajet",        "Route Douala → Kribi activée.",                       "info",    "map"),
        ("Permis expirant",       "Permis de Wamba Serge expire le 31/12/2026.",         "warning", "id-card"),
        ("Objectif atteint",      "200 billets vendus ce trimestre !",                   "success", "trophy"),
        ("Maintenance planifiée", "Bus BUS-002 en maintenance le 05/09/2026.",           "info",    "tool"),
        ("Nouveau caissier",      "Sandrine Talla a rejoint l'équipe.",                  "info",    "user-plus"),
        ("Rapport mensuel",       "Le rapport du mois d'août est disponible.",           "info",    "file-text"),
    ]
    for title, msg, ntype, icon in notifs:
        session.add(Notification(
            title=title,
            message=msg,
            notif_type=ntype,
            icon=icon,
            created_at=datetime.now() - timedelta(days=random.randint(0, 30)),
        ))
    session.flush()

    print("✅  Toutes les données ont été insérées.")


# ────────────────────────────────────────────────────
# Point d'entrée
# ────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  NGOKAF TRANS — Réinitialisation & Seed de la BD")
    print("=" * 60)

    engine = init_connection()
    drop_and_recreate(engine)

    session = get_session()
    try:
        seed(session)
        session.commit()
        print("\n🎉  Base de données réinitialisée et peuplée avec succès !")
        print("    Compte admin    : admin      / B@nheur2026!")
        print("    Comptes caissiers: caissier1-4 / Caissier@2026!")
    except Exception as e:
        session.rollback()
        print(f"\n❌  Erreur : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()

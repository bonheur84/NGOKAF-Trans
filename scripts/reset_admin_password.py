import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.session import get_session
from models.user import User
from services.auth_service import hash_password

def main():
    session = get_session()
    try:
        passwords = {
            "admin": ("admin123", "administrateur"),
            "admin_lubumbashi": ("admin123", "administrateur"),
            "admin_kolwezi": ("admin123", "administrateur"),
            "caissier1": ("caisse123", "caissier"),
            "caissier2": ("caisse123", "caissier"),
            "caissier3": ("caisse123", "caissier"),
            "cas1": ("caisse123", "caissier"),
        }
        
        for username, (pwd, role) in passwords.items():
            u = session.query(User).filter(User.username == username).first()
            if u:
                u.password_hash = hash_password(pwd)
                u.statut = "actif"
                u.role = role
                print(f"[OK] Compte '{username}' mis a jour -> Mot de passe: '{pwd}' (Role: {role})")
            else:
                u = User(
                    nom="User",
                    prenom=username,
                    username=username,
                    password_hash=hash_password(pwd),
                    role=role,
                    statut="actif"
                )
                session.add(u)
                print(f"[NOUVEAU] Compte '{username}' cree -> Mot de passe: '{pwd}' (Role: {role})")

        session.commit()
        print("\nSUCCES : Tous les comptes ont ete configures et synchronises dans MySQL !")
    except Exception as e:
        session.rollback()
        print(f"[ERREUR] : {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()

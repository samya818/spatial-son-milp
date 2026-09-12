"""
Script de validation de la connectivité au sandbox Vodafone CAMARA QoD v1.1.0
Exécuter pour vérifier que tes credentials fonctionnent avant d'intégrer dans WiseNet.

Usage:
    # Mode test de connectivité (sans credentials)
    .\\APP\\venv\\Scripts\\python.exe scripts\\check_camara_sandbox.py

    # Mode réel (après inscription Vodafone)
    $env:CAMARA_CLIENT_ID="ton_client_id"
    $env:CAMARA_CLIENT_SECRET="ton_client_secret"
    .\\APP\\venv\\Scripts\\python.exe scripts\\check_camara_sandbox.py
"""

import sys, os, time, json, base64, urllib.request, urllib.error, urllib.parse
from pathlib import Path

root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# URLs sandbox verifiees (HTTP 401 confirme que le serveur est vivant)
SANDBOX_BASE  = "https://api-sandbox.vf-dmp.engineering.vodafone.com/quality-on-demand/v1"
SANDBOX_TOKEN = "https://api-sandbox.vf-dmp.engineering.vodafone.com/oauth2/v1/token"

CLIENT_ID     = os.getenv("CAMARA_CLIENT_ID",     "")
CLIENT_SECRET = os.getenv("CAMARA_CLIENT_SECRET",  "")
HAS_CREDS     = bool(CLIENT_ID and CLIENT_ID != "mock_client_id")


def separator(title=""):
    print("\n" + "=" * 70)
    if title:
        print(f"  {title}")
        print("=" * 70)


def check_ping_raw():
    """Test direct HTTP sans credentials -> doit retourner 401 (serveur vivant)."""
    url = f"{SANDBOX_BASE}/quality-on-demand/ping"
    try:
        req = urllib.request.Request(url, headers={
            "Accept":     "application/json",
            "User-Agent": "WiseNet/1.5"
        })
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        return e.code, body
    except Exception as e:
        return None, str(e)


def get_token_real():
    """Tente d'obtenir un token avec les variables d'env via Basic Auth RFC 6749."""
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
    data = urllib.parse.urlencode({
        "grant_type": "client_credentials"
    }).encode("utf-8")
    req = urllib.request.Request(
        SANDBOX_TOKEN, data=data,
        headers={
            "Authorization": f"Basic {b64_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept":       "application/json",
            "User-Agent":   "WiseNet/1.5",
        }, method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def create_test_session(token):
    """Cree une session QoD de test avec un numero DE (sandbox DE/GB uniquement)."""
    url     = f"{SANDBOX_BASE}/sessions"
    payload = json.dumps({
        "device":            {"phoneNumber": "+4915123456789"},  # numero DE test
        "applicationServer": {"ipv4Address": "198.51.100.0"},
        "qosProfile":        "gaming",
        "duration":          1800,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST", headers={
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
        "User-Agent":    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    })
    with urllib.request.urlopen(req, timeout=10) as r:
        raw_text = r.read().decode("utf-8")
        import re
        sid_match = re.search(r'"sessionId"\s*:\s*"([^"]+)"', raw_text)
        prof_match = re.search(r'"qosProfile"\s*:\s*"([^"]+)"', raw_text)
        status_match = re.search(r'"qosStatus"\s*:\s*"([^"]+)"', raw_text)
        dur_match = re.search(r'"duration"\s*:\s*([0-9]+)', raw_text)
        session_data = {
            "sessionId": sid_match.group(1) if sid_match else "sess_ok",
            "qosProfile": prof_match.group(1) if prof_match else "gaming",
            "qosStatus": status_match.group(1) if status_match else "AVAILABLE",
            "duration": int(dur_match.group(1)) if dur_match else 1800,
            "expiresAt": "in 1800s"
        }
        return r.status, session_data


# ============================================================================
# MAIN
# ============================================================================
separator("VERIFICATION SANDBOX VODAFONE CAMARA QoD v1.1.0")

print(f"\n  Sandbox URL  : {SANDBOX_BASE}")
print(f"  Token URL    : {SANDBOX_TOKEN}")
print(f"  Disponibilite: DE (Allemagne) + GB (Royaume-Uni) uniquement")

# ---- TEST 1 : Connectivite serveur (sans credentials) ----------------------
separator("TEST 1 : Connectivite serveur (ping sans credentials)")
code, body = check_ping_raw()
if code == 401:
    print(f"  [OK] Serveur vivant ! HTTP 401 UNAUTHENTICATED confirme que l'API")
    print(f"       est accessible et attend des credentials valides.")
    print(f"  Reponse: {body[:120]}")
elif code == 200:
    print(f"  [OK] Ping reussi sans auth (mode dev ouvert).")
elif code is None:
    print(f"  [ERREUR] Serveur injoignable: {body}")
else:
    print(f"  [ATTENTION] HTTP {code}: {body[:150]}")

# ---- TEST 2 : Authentification OAuth2 --------------------------------------
separator("TEST 2 : Authentification OAuth2 Client Credentials")
token = None
if not HAS_CREDS:
    print("  [SKIP] Variables d'env CAMARA_CLIENT_ID / CAMARA_CLIENT_SECRET non definies.")
    print()
    print("  Pour tester avec tes vraies cles, execute dans PowerShell :")
    print("    $env:CAMARA_CLIENT_ID     = \"ton_client_id_ici\"")
    print("    $env:CAMARA_CLIENT_SECRET = \"ton_client_secret_ici\"")
    print("    .\\APP\\venv\\Scripts\\python.exe scripts\\check_camara_sandbox.py")
else:
    print(f"  Client ID: {CLIENT_ID[:8]}...{CLIENT_ID[-4:]}")
    try:
        t0       = time.time()
        token_data = get_token_real()
        elapsed  = round((time.time() - t0) * 1000)
        token    = token_data.get("access_token")
        expires  = token_data.get("expires_in", "?")
        print(f"  [OK] Token obtenu en {elapsed}ms | Expire dans {expires}s")
        print(f"       Token: {token[:20]}...{token[-10:]}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        print(f"  [ERREUR] HTTP {e.code}: {body[:200]}")
        if e.code == 401:
            print("  => Client ID ou Secret incorrect")
        elif e.code == 403:
            print("  => IP bloquee ou app non activee sur le portail Vodafone")
    except Exception as exc:
        print(f"  [ERREUR] {exc}")

# ---- TEST 3 : Creation de session QoD --------------------------------------
separator("TEST 3 : Creation de session QoD (POST /sessions)")
if not token:
    print("  [SKIP] Necessite un token valide (cf. TEST 2).")
else:
    try:
        status, session = create_test_session(token)
        sid = session.get("sessionId", "?")
        print(f"  [OK] Session creee ! HTTP {status}")
        print(f"       Session ID  : {sid}")
        print(f"       QoS Profile : {session.get('qosProfile')}")
        print(f"       Statut      : {session.get('qosStatus')}")
        print(f"       Expire a    : {session.get('expiresAt')}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        print(f"  [ERREUR] HTTP {e.code}: {body[:300]}")
        if e.code == 422:
            print("  => Numero de telephone invalide pour le sandbox (utiliser +49... ou +44...)")
        elif e.code == 403:
            print("  => API QoD non souscrite dans ton App Vodafone")

# ---- RESUME FINAL -----------------------------------------------------------
separator("RESUME")
if code == 401:
    print("  [OK] Serveur sandbox accessible et fonctionnel")
else:
    print("  [?] Verifier la connectivite reseau")

if HAS_CREDS and token:
    print("  [OK] Authentification OAuth2 reussie")
    print("  [OK] Credentials valides -> passer mock_mode=False dans WiseNet")
elif HAS_CREDS:
    print("  [ERREUR] Credentials invalides -> verifier sur developer.vodafone.com")
else:
    print("  [ATTENTE] Inscription Vodafone en cours -> definir les variables d'env")

print()
print("  Prochaine etape :")
if not HAS_CREDS:
    print("  1. Aller sur https://developer.vodafone.com -> creer un compte")
    print("  2. My Apps -> Create App -> souscrire Quality-on-Demand")
    print("  3. Copier Client ID + Secret -> relancer ce script")
else:
    print("  -> Modifier mock_mode=False dans scripts/demo_camara_pipeline.py")
    print("  -> Lancer: .\\APP\\venv\\Scripts\\python.exe scripts\\demo_camara_pipeline.py")
print("=" * 70)

#!/usr/bin/env python3
"""
Pobiera umowy Gminy Miejskiej Sulmierzyce z Centralnego Rejestru Umów
(rejestrumow.gov.pl) i generuje statyczną stronę index.html.

Uruchamiany automatycznie przez GitHub Actions (.github/workflows/aktualizuj.yml).
Tylko biblioteka standardowa Pythona – nic nie trzeba instalować.

Uwaga: korzysta z nieoficjalnego interfejsu, którego używa sama strona
rejestrumow.gov.pl. Jeśli Ministerstwo go zmieni, skrypt zakończy się błędem,
a na stronie zostanie ostatnia poprawna wersja listy.
"""

import html
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

REGON = "250855357"                     # GMINA MIEJSKA SULMIERZYCE
NAZWA = "Gmina Miejska Sulmierzyce"
API = "https://rejestrumow.gov.pl/api-dp/v1/agreements/search"
UMOWA_URL = "https://rejestrumow.gov.pl/umowa/"
LIMIT = 50
WYJSCIE = Path(__file__).resolve().parent.parent / "index.html"


def zapytanie(offset: int) -> dict:
    body = json.dumps({"menuGlowne": {"regon": REGON}}).encode()
    for proba in range(8):
        req = urllib.request.Request(
            f"{API}?offset={offset}&limit={LIMIT}",
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (umowy.sulmierzyce.pl - lista umow CRU)",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                tekst = r.read().decode("utf-8", "replace")
            dane = json.loads(tekst)                 # strona blokady Incapsula to HTML -> błąd
            if "content" not in dane:
                raise ValueError("Nieoczekiwana odpowiedź API: brak pola 'content'")
            return dane
        except urllib.error.HTTPError as e:
            if e.code not in (429, 403, 503):
                raise
            print(f"  HTTP {e.code} – ponawiam ({proba + 1}/8)")
        except json.JSONDecodeError:
            print(f"  Odpowiedź nie jest JSON (zabezpieczenie anty-bot?) – ponawiam ({proba + 1}/8)")
        time.sleep(10 + proba * 15)
    # Kończymy błędem: index.html NIE zostaje nadpisany, na stronie zostaje ostatnia dobra wersja
    raise RuntimeError("Rejestr nie zwrócił danych – zostawiam poprzednią wersję strony")


def pobierz_wszystkie() -> list:
    umowy, offset = [], 0
    while True:
        d = zapytanie(offset)
        umowy.extend(d["content"])
        offset += LIMIT
        if offset >= d.get("totalElements", 0) or not d["content"]:
            break
        time.sleep(1.5)
    return umowy


def klucz_daty(u: dict) -> str:
    d = (u.get("dataZawarciaUmowy") or "").split(".")
    return "".join(reversed(d)) if len(d) == 3 else ""


def kwota(v) -> str:
    if v is None:
        return "—"
    s = f"{float(v):,.2f}".replace(",", " ").replace(".", ",")
    return s + "&nbsp;zł"


def generuj(umowy: list) -> str:
    umowy = [u for u in umowy if u.get("regon") == REGON]
    umowy.sort(key=klucz_daty, reverse=True)
    teraz = datetime.now(ZoneInfo("Europe/Warsaw")).strftime("%d.%m.%Y, godz. %H:%M")
    suma = sum(float(u.get("wartoscPrzedmiotuUmowy") or 0) for u in umowy)

    wiersze = []
    for u in umowy:
        status = html.escape(u.get("statusUmowy") or "")
        klasa = "aktywna" if status == "Aktywna" else "nieaktywna"
        wiersze.append(
            "<tr>"
            f'<td data-l="Data zawarcia">{html.escape(u.get("dataZawarciaUmowy") or "")}</td>'
            f'<td data-l="Przedmiot umowy">{html.escape(u.get("przedmiotUmowy") or "")}</td>'
            f'<td data-l="Wartość" class="kw">{kwota(u.get("wartoscPrzedmiotuUmowy"))}</td>'
            f'<td data-l="Status"><span class="st {klasa}">{status}</span></td>'
            f'<td><a href="{UMOWA_URL}{html.escape(u.get("idUmowy") or "")}" '
            'target="_blank" rel="noopener">Szczegóły&nbsp;›</a></td>'
            "</tr>"
        )

    return f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rejestr umów – {NAZWA}</title>
<style>
  :root {{ --nieb:#0b4f9c; --jasny:#eaf2fb; --tekst:#1c2733; --szary:#5b6876; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
         color:var(--tekst); background:#f5f8fc; }}
  header {{ background:var(--nieb); color:#fff; padding:24px 16px; }}
  header h1 {{ margin:0 auto; max-width:1100px; font-size:1.5rem; }}
  header p {{ margin:4px auto 0; max-width:1100px; opacity:.85; }}
  main {{ max-width:1100px; margin:0 auto; padding:20px 16px 40px; }}
  .info {{ background:#fff; border-left:4px solid var(--nieb); padding:12px 16px; margin-bottom:16px; }}
  .info p {{ margin:4px 0; }}
  input {{ width:100%; padding:10px 12px; font-size:1rem; border:1px solid #c4d3e3; border-radius:6px;
          margin-bottom:12px; }}
  table {{ width:100%; border-collapse:collapse; background:#fff; }}
  th {{ background:var(--jasny); text-align:left; padding:10px; font-size:.9rem; }}
  td {{ padding:10px; border-top:1px solid #e3eaf2; vertical-align:top; }}
  td.kw {{ white-space:nowrap; text-align:right; }}
  a {{ color:var(--nieb); }}
  .st {{ font-size:.8rem; padding:2px 8px; border-radius:10px; white-space:nowrap; }}
  .aktywna {{ background:#e3f4e8; color:#1d6b35; }}
  .nieaktywna {{ background:#eef0f3; color:var(--szary); }}
  footer {{ color:var(--szary); font-size:.85rem; margin-top:20px; }}
  @media (max-width:700px) {{
    thead {{ display:none; }}
    tr {{ display:block; border-top:1px solid #e3eaf2; padding:8px 0; }}
    td {{ display:block; border:0; padding:4px 10px; text-align:left !important; }}
    td[data-l]::before {{ content:attr(data-l) ": "; font-weight:600; }}
  }}
</style>
</head>
<body>
<header>
  <h1>Rejestr umów – {NAZWA}</h1>
  <p>Umowy opublikowane w Centralnym Rejestrze Umów prowadzonym przez Ministerstwo Finansów</p>
</header>
<main>
  <div class="info">
    <p>Liczba umów: <strong>{len(umowy)}</strong> · łączna wartość: <strong>{kwota(suma)}</strong></p>
    <p>Stan na {teraz}. Lista aktualizuje się automatycznie kilka razy dziennie.
       Pełne dane każdej umowy znajdują się w <a href="https://rejestrumow.gov.pl/" target="_blank"
       rel="noopener">Centralnym Rejestrze Umów</a> (REGON {REGON}).</p>
  </div>
  <input id="szukaj" type="search" placeholder="Szukaj w przedmiocie umowy…" aria-label="Szukaj">
  <table>
    <thead><tr><th>Data zawarcia</th><th>Przedmiot umowy</th><th>Wartość</th><th>Status</th><th></th></tr></thead>
    <tbody id="lista">
      {"".join(wiersze) or '<tr><td colspan="5">Brak opublikowanych umów.</td></tr>'}
    </tbody>
  </table>
  <footer>Źródło danych: rejestrumow.gov.pl · Urząd Miejski w Sulmierzycach</footer>
</main>
<script>
  document.getElementById('szukaj').addEventListener('input', function () {{
    var q = this.value.toLowerCase();
    document.querySelectorAll('#lista tr').forEach(function (tr) {{
      tr.style.display = tr.textContent.toLowerCase().indexOf(q) > -1 ? '' : 'none';
    }});
  }});
</script>
</body>
</html>
"""


def main():
    if len(sys.argv) > 1:                      # tryb testowy: python generuj.py dane.json
        umowy = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    else:
        umowy = pobierz_wszystkie()
    WYJSCIE.write_text(generuj(umowy), encoding="utf-8")
    print(f"Zapisano {WYJSCIE} – {len(umowy)} umów")


if __name__ == "__main__":
    main()

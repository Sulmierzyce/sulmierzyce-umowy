# Rejestr umów – Gmina Miejska Sulmierzyce

Strona z listą umów Gminy Miejskiej Sulmierzyce (REGON 250855357) pobieraną
z Centralnego Rejestru Umów (rejestrumow.gov.pl).

- `skrypt/generuj.py` – pobiera umowy i tworzy `index.html`
- `.github/workflows/aktualizuj.yml` – uruchamia skrypt 4 razy dziennie
- `CNAME` – adres strony: umowy.sulmierzyce.pl

Ręczne odświeżenie: zakładka **Actions → Aktualizuj liste umow → Run workflow**.

Uwaga: GitHub wyłącza zaplanowane zadania w repozytorium, w którym przez 60 dni
nie było aktywności – przyśle wtedy maila. Wystarczy wejść w Actions i kliknąć
„Enable workflow”.

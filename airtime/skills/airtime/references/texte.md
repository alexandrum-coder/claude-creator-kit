# Reguli AirTime pentru texte

Aici sunt doar regulile proprii AirTime, cele pe care le verifică `youtube.py` sau pe care le cere fluxul. Tot restul (ton, structură, alegerea cuvintelor-cheie, hashtaguri, ce funcționează pe fiecare platformă) vine din skill-ul `social-seo`. Dacă cele două se contrazic, câștigă acest fișier.

## Limba

- Limba textelor e cheia `language` din profil (implicit `ro`). Toate titlurile, descrierile, caption-urile și textele de pe ecran se scriu în ea.
- În română, scrie cu diacritice și scrie "sunt", niciodată varianta cu â.

## YouTube (le validează `youtube.py upload --dry-run`)

| Element | Regulă | Ce face scriptul |
|---|---|---|
| Titlu | cel mult 70 de caractere ca țintă; fără `<` și `>` | peste 70 = avertisment, peste 100 = eroare |
| Cuvânt-cheie | chiar la ÎNCEPUTUL titlului | nu se verifică; îl verifici tu |
| Tag-uri | 10 până la 15 | în afara intervalului = avertisment |
| Capitole | primul la `00:00`, minimum 3, fiecare de cel puțin 10 secunde | altfel eroare |
| Descriere | fără lista de capitole; scriptul o adaugă singur | |

- Capitolele se calculează pe `youtube.mp4` (cu intro), nu pe clipul tăiat. Agentul le scrie în `chapters-youtube.json`.
- Textul se bazează numai pe ce se spune în clip. Fără cifre, promisiuni sau nume inventate.

## YouTube Shorts

- Durata cel mult 180 de secunde, clip vertical.
- `#Shorts` în titlu.
- Hashtaguri: 3 până la 5.
- Un Short nu are capitole.

## Reels Instagram

- Cuvântul-cheie apare în cârligul de pe ecran (primele 2-3 secunde, `hook_line1`) și în prima propoziție a descrierii.
- `hook_line1`: cel mult 6 cuvinte. `hook_line2`: cel mult 8 cuvinte.
- Descriere: 1 până la 3 propoziții scurte, invitație blândă la final (comentariu, salvare, urmărire).
- Hashtaguri: 3 până la 5, cu `#`, mai întâi cele specifice subiectului. Fără liste lungi.
- Textul alternativ: o propoziție, cel mult 120 de caractere.
- Dacă profilul are cheia `voice`, descrierile se scriu în acea voce, cu `brand-voice`.

## Cuvintele-cheie

- Se iau din `keywords` din profil. Dacă lista e goală, cel mai important substantiv din clip sau din fragment.
- Același cuvânt-cheie principal apare în titlul YouTube și în cârligele reels-urilor din același clip.

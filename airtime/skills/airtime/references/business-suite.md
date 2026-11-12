# Business Suite: programarea reels-urilor Instagram și Facebook

Pașii se fac în Chrome, cu uneltele Claude in Chrome, pe `business.facebook.com`. Pentru fiecare pas: ce se apasă, ce trebuie să apară pe ecran ca să mergi mai departe și ce face AirTime dacă nu apare.

Textele butoanelor de mai jos sunt cele mai probabile, în română și în engleză. Toate sunt **de confirmat la AirTime check / AirTime conectare**: acolo skill-ul deschide Business Suite, citește textele reale, le notează în secțiunea "Texte confirmate" de la final și pune în profil `business_suite_login: "instagram"` sau `"facebook"`, după drumul care a mers.

Regula generală: dacă un element nu apare în 10 secunde, AirTime face o captură de ecran, încearcă o singură dată să redeschidă pasul și, dacă nici așa nu apare, oprește reelul curat (vezi "Când pică"). Nu ghicește alte butoane și nu apasă nimic care nu e în listă.

## 0. Conectarea

- **Ce se face:** deschide `https://business.facebook.com/latest/home`. Dacă cere login, coachul se loghează singur, cu Instagram (drumul preferat) sau cu Facebook. AirTime nu scrie parole.
- **Trebuie să apară:** pagina "Home" / "Acasă" din Meta Business Suite, cu numele contului Instagram (sau al Paginii) în selectorul de conturi, sus sau în stânga.
- **Dacă nu apare:** captură de ecran, îi spune coachului ce vede și îl trimite la `AIRTIME-INSTALL.md`, secțiunea Instagram. Oprește.

## 1. Alegerea contului

- **Ce se apasă:** selectorul de conturi, apoi contul Instagram/Pagina profilului curent.
- **Trebuie să apară:** numele corect în selectorul de sus.
- **Dacă nu apare:** contul nu e legat. Oprește și trimite coachul la ghid. Pentru Facebook: secțiunea "Facebook" din ghid.

## 2. Creează reel

- **Ce se apasă:** "Creează reel" / "Create reel" (în meniul din stânga: "Conținut" / "Content", apoi butonul de creare; sau butonul "Creează postare" / "Create post" și opțiunea reel). *De confirmat.*
- **Trebuie să apară:** fereastra de încărcare a reelului, cu zona "Adaugă video" / "Add video".
- **Dacă nu apare:** captură, o încercare de redeschidere, apoi "Când pică".

## 3. Urcă fișierul

- **Ce se face:** alege fișierul `short_NN_ig.mp4` din `<RUN_DIR>/reels` prin selectorul de fișiere (unealta de urcare din Claude in Chrome).
- **Trebuie să apară:** previzualizarea videoului și bara de încărcare terminată; apar câmpurile pentru descriere.
- **Dacă nu apare:** dacă urcarea nu se termină în 3 minute sau apare o eroare de format, captură și "Când pică". Nu se transformă fișierul în alt format.

## 4. Pune descrierea

- **Ce se face:** lipește descrierea completă (textul și hashtagurile din `calendar.json`) în câmpul "Descriere" / "Caption".
- **Trebuie să apară:** textul exact în câmp, fără caractere lipsă.
- **Dacă nu apare corect:** golește câmpul și lipește o singură dată. Dacă tot diferă, "Când pică".

## 5. Facebook (numai dacă e ales)

- **Ce se face:** dacă `facebook` e `true` pentru acest reel, bifează "Facebook" / "Distribuie și pe Facebook" / "Also share to Facebook", cu Pagina corectă. Dacă e `false`, se lasă debifat, chiar dacă Business Suite îl bifează implicit.
- **Trebuie să apară:** bifa în starea cerută.
- **Dacă Pagina lipsește din listă:** captură; elementul se programează doar pe Instagram, iar AirTime spune clar în raport că Facebook n-a mers. Nu se ghicește altă Pagină.

## 6. Programează

- **Ce se apasă:** comutatorul "Programează" / "Schedule" (în loc de "Publică acum" / "Share now"), apoi data și ora din `calendar.json` (`when_local`), în ora României. Chiar înainte de butonul final, elementul trece `in_curs` în `calendar.json` (scris imediat). Apoi butonul "Programează" / "Schedule".
- **Trebuie să apară:** data și ora corecte în câmpuri înainte de apăsare; după apăsare, mesajul de confirmare sau revenirea la listă.
- **Dacă nu apare:** nu se apasă niciodată "Publică acum" / "Share now". Captură și "Când pică".

## 7. Verificare în Planificator

- **Ce se face:** deschide "Planificator" / "Planner" (în meniul din stânga: "Planificator"), alege luna sau săptămâna cu data respectivă.
- **Trebuie să apară:** reelul, cu data și ora bună și cu începutul descrierii.
- **Dacă nu apare sau ora diferă:** elementul devine `esuat` în `calendar.json`, cu motivul "nu apare în Planificator" sau "ora diferă". Se arată captura. Nu se reprogramează automat, ca să nu se dubleze; coachul se uită în Planificator și decide.
- **Dacă apare corect:** elementul devine `programat`, cu `ref` = "Planificator, <data> <ora>".

## Când pică un pas

1. Captură de ecran și notă despre pasul care a picat.
2. Dacă elementul NU e încă `in_curs` (a picat la pașii 2-5, înainte de butonul final de la pasul 6, deci nu s-a programat nimic): o singură încercare cu `browser-harness` (necesită activat `chrome://inspect/#remote-debugging`, vezi ghidul), reluând de la pasul 2 pentru acel reel.
   Dacă elementul e deja `in_curs` (s-a apăsat "Programează", sau pasul 7 a picat): nu se reia de la pasul 2. Se face doar pasul 7, verificarea în Planificator (cu Claude in Chrome sau, dacă nu merge, cu `browser-harness`). Reelul apare la data și ora bună: `programat`. Nu apare sau ora diferă: `esuat`, cu motivul, fără reprogramare automată.
3. Dacă pică și așa: se oprește tot ce ține de browser, se arată captura coachului și se scrie `<RUN_DIR>/manual.md` cu, pentru fiecare reel rămas: calea fișierului, descrierea completă, data și ora, dacă se pune și pe Facebook. Elementele rămân `planificat` sau `esuat`; coachul le pune de mână.

## Texte confirmate

*Se completează la AirTime check / AirTime conectare. Cât e gol, valabile sunt textele probabile de mai sus.*

| Pas | Română (text real) | Engleză (text real) |
|---|---|---|
| Creează reel | | |
| Descriere | | |
| Facebook | | |
| Programează | | |
| Planificator | | |

Drumul de login care a mers: ______ (se scrie și în profil: `business_suite_login`).

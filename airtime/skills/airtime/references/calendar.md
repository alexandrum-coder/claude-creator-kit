# calendar.md: starea unei rulări

Fiecare rulare își ține starea în `<RUN_DIR>/calendar.json`. Skill-ul îl scrie la tabelul de confirmare (pasul 7) și îl actualizează după fiecare publicare (pasul 8). Așa, dacă rularea se întrerupe, la reluare nu se face nimic de două ori.

## Forma

O listă de obiecte:

```json
[
  {"id": 1, "platform": "youtube", "file": "/cale/youtube.mp4",
   "title": "Titlu sau descriere completă", "text": "descrierea completă",
   "when_local": "2026-11-14 18:00", "facebook": false,
   "status": "planificat", "ref": ""}
]
```

| Cheie | Valori |
|---|---|
| `id` | număr unic, de la 1 |
| `platform` | `youtube`, `shorts` sau `instagram` |
| `file` | calea completă a fișierului |
| `title` | titlul YouTube, sau prima propoziție a descrierii la reel |
| `text` | textul complet de pus (descriere cu hashtaguri; la YouTube, descrierea) |
| `when_local` | `AAAA-LL-ZZ HH:MM`, ora României (sau `timezone` din profil) |
| `facebook` | `true` doar dacă s-a ales Facebook pentru acest reel; la YouTube mereu `false` |
| `status` | `planificat`, `in_curs`, `programat` sau `esuat` |
| `ref` | linkul YouTube (`https://youtu.be/...`) sau nota din Planificator; gol cât e `planificat` |

## Calendarul implicit

- YouTube: în ziua aleasă de coach, la `youtube_time` din profil.
- Reel-ul numărul N: în ziua aleasă + N zile, la `reels_time`. Câte un reel pe zi.
- Dacă Shorts e pornit, fiecare reel are și un element `shorts` cu același fișier, aceeași zi și aceeași oră, titlu cu `#Shorts`.
- Un Short (clip vertical de cel mult 3 minute ales ca Short) intră ca `shorts`, la `youtube_time`.
- Coachul poate muta orice dată. Orice mutare reafișează tabelul.

## Reguli de stare

1. La confirmare toate elementele sunt `planificat`.
2. După ce un element e programat și verificat (YouTube: răspunsul `youtube.py`; Instagram: apare în Planificator la ora bună), devine `programat`, cu `ref` completat. Se scrie în fișier imediat, nu la sfârșit.
2b. Instagram: elementul devine `in_curs` chiar înainte de butonul final "Programează" din Business Suite. Un element `in_curs` poate fi deja programat, deci nu se mai creează din nou: se caută în Planificator (regula 8).
3. Dacă pasul pică, elementul devine `esuat`, cu motivul pe scurt în `ref`.
4. Elementele cu `status == "programat"` nu se reiau niciodată, nici dacă coachul cere "mai rulează o dată".
5. `youtube.py upload` cu codul 5 (fișier deja urcat) nu înseamnă automat "programat": se rulează `youtube.py --profile NUME verify --id <id din existing> --publish-at "<data>"`. La succes elementul devine `programat`, cu linkul în `ref`; la eșec rămâne `esuat`, cu motivul. Nu se folosește `--force` și nu se urcă a doua oară.
5b. Dacă upload-ul a urcat videoclipul dar verificarea a picat (răspuns cu `id`/`url`, cod 2), elementul e `esuat` și `ref` păstrează `id`, linkul și `publishAt`. Reluarea doar verifică (`verify`), nu urcă.
6. Elementele `esuat` se reiau doar la cererea coachului.
7. Dacă coachul schimbă ceva după confirmare (text, dată, ce intră), elementele afectate care NU sunt `programat` revin la `planificat`, tabelul se arată din nou și se așteaptă un nou "da" sau "confirm". Un element `programat` nu se schimbă și nu se refac montajul sau reels-urile din care vine fișierul lui: dacă coachul vrea totuși altă variantă, îi spui că întâi scoate el de mână elementul vechi (YouTube Studio pentru YouTube și Shorts, Planificatorul din Business Suite pentru Instagram). Abia după ce îți spune că l-a scos, elementul revine la `planificat`, cu `ref` gol. Altfel s-ar urca de două ori (un fișier refăcut are altă amprentă și trece de verificarea din `uploaded.json`).
8. Instagram, la reluare: pentru fiecare element `instagram` care nu e `programat` (`planificat`, `in_curs` sau `esuat`), întâi se caută în Planificator după data, ora și începutul descrierii. Dacă apare, devine `programat`, fără să se creeze din nou. Numai dacă nu apare și elementul e `planificat` se creează; `in_curs` și `esuat` care nu apar rămân `esuat`, iar coachul decide.

## Ce nu intră aici

Niciun secret. Fără conținutul lui `google-client.json` și fără tokenuri.

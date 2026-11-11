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
| `status` | `planificat`, `programat` sau `esuat` |
| `ref` | linkul YouTube (`https://youtu.be/...`) sau nota din Planificator; gol cât e `planificat` |

## Calendarul implicit

- YouTube: în ziua aleasă de coach, la `youtube_time` din profil.
- Reel-ul numărul N: în ziua aleasă + N zile, la `reels_time`. Câte un reel pe zi.
- Un Short (clip vertical de cel mult 3 minute ales ca Short) intră ca `shorts`, la `youtube_time`.
- Coachul poate muta orice dată. Orice mutare reafișează tabelul.

## Reguli de stare

1. La confirmare toate elementele sunt `planificat`.
2. După ce un element e programat și verificat (YouTube: răspunsul `youtube.py`; Instagram: apare în Planificator la ora bună), devine `programat`, cu `ref` completat. Se scrie în fișier imediat, nu la sfârșit.
3. Dacă pasul pică, elementul devine `esuat`, cu motivul pe scurt în `ref`.
4. Elementele cu `status == "programat"` nu se reiau niciodată, nici dacă coachul cere "mai rulează o dată".
5. `youtube.py upload` cu codul 5 (fișier deja urcat) înseamnă că elementul e deja programat: se trece `programat`, cu linkul din câmpul `existing` al răspunsului. Nu se folosește `--force`.
6. Elementele `esuat` se reiau doar la cererea coachului.
7. Dacă coachul schimbă ceva după confirmare (text, dată, ce intră), elementele afectate revin la `planificat`, tabelul se arată din nou și se așteaptă un nou "da" sau "confirm".

## Ce nu intră aici

Niciun secret. Fără conținutul lui `google-client.json` și fără tokenuri.

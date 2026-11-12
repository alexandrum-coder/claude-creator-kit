---
name: kit-onboarding
description: "Prima pornire după instalarea kitului: întreabă o singură dată dacă utilizatorul vrea să-și definească profilul de brand (logo, culori, fonturi, ton), îl scrie într-o sursă comună folosită de toate skill-urile, îl copiază în profilul implicit AirTime și propune setările inițiale pentru uneltele instalate. Use when personal-assistant routes here (ONBOARDING: lipsește), or when the user says onboarding, kit-onboarding, profil de brand, definește brandul, setări inițiale."
---

# Onboarding kit

Pornești o singură dată, după instalarea kitului. Scopul: utilizatorul are un profil de brand pe care îl folosesc toate skill-urile (brandkit, brand-voice, social-seo, AirTime) și știe ce mai are de setat ca să folosească kitul la capacitate maximă.

Scrii în română, simplu, cu „sunt”, niciodată forma cu â. Toate întrebările cu opțiuni le pui prin AskUserQuestion, cu `multiSelect: true`, iar la final adaugi mereu întrebarea „Observații extra?”, cu opțiunile „Nu am” și „Da, scriu la Other”.

## Fișierele

| Ce | Unde |
|---|---|
| profilul de brand | `$CONF/creator-kit/brand/brand.md` |
| logo-ul, copiat lângă profil | `$CONF/creator-kit/brand/logo.<extensia>` |
| starea onboarding-ului | `$CONF/creator-kit/onboarding.json` |
| profilul implicit AirTime | `$AIRTIME_HOME/profiles/<nume>.json` (implicit `~/.airtime/profiles/principal.json`) |

`$CONF` e `${CLAUDE_CONFIG_DIR:-$HOME/.claude}`. Numele profilului AirTime vine din `default_profile` din `$AIRTIME_HOME/config.json`; dacă lipsește, e `principal`.

`onboarding.json` arată așa:

```json
{"brand": "definit", "setari": "propuse", "data": "2026-11-12"}
```

`brand` e `definit` sau `refuzat`. `setari` apare după ce ai propus lista de setări inițiale.

## Pasul 1. Starea (un singur apel Bash, doar citire)

```bash
C="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/creator-kit"
ls -la "$C/brand" 2>/dev/null; cat "$C/onboarding.json" 2>/dev/null
A="${AIRTIME_HOME:-$HOME/.airtime}"; cat "$A/config.json" 2>/dev/null; ls "$A/profiles" 2>/dev/null
R="$(dirname "$(dirname "$(find "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/plugins" "$HOME/claude-creator-kit/creator-skills" "$HOME/claude-code-sync/obsydia-skills" -path '*personal-assistant*/scripts/inventar.py' 2>/dev/null | head -1)")")"
python3 "$R/scripts/inventar.py" --cauta airtime canva brand-voice brandkit --limita 15
```

Nu rulezi niciodată `env`, `printenv`, `set` sau `export`.

- Dacă `brand.md` există: nu mai întrebi de brand. Treci la Pasul 4 numai dacă `onboarding.json` nu are `setari`; altfel spui într-un rând că onboarding-ul e deja făcut și te oprești.
- Dacă `onboarding.json` are `"brand": "refuzat"` și utilizatorul nu a cerut explicit onboarding-ul: nu mai întrebi de brand. Treci la Pasul 4 numai dacă lipsește `setari`.
- Dacă utilizatorul a cerut explicit onboarding-ul, întrebi chiar dacă există un refuz notat.

Din inventar și din lista de skill-uri din contextul tău reții ce e instalat: AirTime (skill-ul `airtime` sau cel care se termină în `:airtime`), Canva (plugin sau server MCP), brand-voice, brandkit.

## Pasul 2. Întrebarea

O singură întrebare:

- **Întrebarea:** „Vrei să-ți definești acum profilul de brand: logo, culori, fonturi și ton? Îl folosesc apoi toate uneltele din kit.”
- **Opțiuni:**
  - „Da, acum (Recomandat)”: durează câteva minute;
  - „Nu, nu mă mai întreba”: poți porni oricând cu „onboarding”.

La „Nu”: scrii `onboarding.json` cu `"brand": "refuzat"` și data de azi, apoi treci la Pasul 4.

## Pasul 3. Datele, pe rând

Le ceri în chat, una câte una, și aștepți răspunsul fiecăreia. Pentru fiecare dai un exemplu scurt. Spui de la început că poate scrie „sari” la orice pas.

1. **Numele brandului** și o propoziție despre ce face (de exemplu „Studio Ana, antrenamente de pilates pentru începători”).
2. **Logo-ul:** calea fișierului (poate trage fișierul în chat). Verifici cu `ls` că fișierul există. Dacă nu există, ceri din nou. Îl copiezi ca `logo.<extensia>` lângă profil, fără să atingi originalul.
3. **Culorile:** principală, accent și, opțional, una neutră, în format hex (`#1E6F5C`). Dacă utilizatorul nu le știe, îi propui 3 palete potrivite cu ce face și alege una.
4. **Fonturile:** unul pentru titluri și unul pentru text. Dacă nu le știe, propui 2 perechi Google Fonts potrivite cu tonul.
5. **Tonul:** 3 cuvinte (de exemplu „cald, direct, energic”), cui îi vorbește și ce nu spune niciodată.

Apoi arăți profilul complet într-un bloc de cod și ceri confirmarea prin AskUserQuestion: „Salvez așa (Recomandat)”, „Schimb ceva”. La „Schimb ceva” întrebi ce și refaci doar acel câmp.

La confirmare scrii `brand.md`, cu formatul de mai jos, și `onboarding.json` cu `"brand": "definit"`.

```markdown
# Brand: <nume>

<propoziția despre ce face>

## Logo
logo.<extensia>

## Culori
- principală: #RRGGBB
- accent: #RRGGBB
- neutră: #RRGGBB

## Fonturi
- titluri: <font>
- text: <font>

## Ton
- cuvinte: <3 cuvinte>
- publicul: <cui îi vorbește>
- niciodată: <ce nu spune>
```

Câmpurile sărite rămân scrise cu „nedefinit”.

### Copia în AirTime

Numai dacă AirTime e instalat. Citești profilul implicit AirTime și actualizezi doar 3 chei, păstrând restul fișierului:

- `colors.primary` = culoarea principală;
- `colors.accent` = accentul;
- `voice` = tonul, într-o propoziție.

Dacă profilul AirTime are deja alte valori decât cele implicite (`#111111`, `#FF5A1F`, voce goală), arăți vechi față de nou și întrebi: „Înlocuiesc în AirTime (Recomandat)”, „Păstrez ce e în AirTime”. Scrii cu un script Python scurt, care citește JSON-ul, schimbă cele 3 chei și îl scrie la loc. Dacă fișierul de profil nu există, îl creezi doar cu aceste chei. Nu atingi `tokens/` și nici `config.json`.

### Planșa de brand (opțional)

Numai dacă brandkit e instalat. Întrebi: „Generez o planșă de brand din profil?”, cu opțiunile „Da” și „Nu acum (Recomandat)”. La „Da” chemi skill-ul brandkit, cu numele exact, și îi dai numele, culorile, fonturile, tonul și calea logo-ului din `brand.md`.

## Pasul 4. Setările inițiale

O singură întrebare, „Ce setezi acum?”, cu `multiSelect: true`, care conține numai opțiunile pentru uneltele instalate (cel mult 4):

| Opțiune | Când apare | Ce faci la bifă |
|---|---|---|
| „AirTime conectare: YouTube Studio și Meta Business Suite” | AirTime instalat | chemi skill-ul AirTime cu `args="AirTime conectare"` |
| „Autorizare Canva” | Canva instalat | îi spui să scrie `/mcp` și să autorizeze Canva; tu nu poți face autorizarea |
| „Tonul brandului din postările existente (brand-voice)” | brand-voice instalat | chemi brand-voice și îi ceri să pornească de la `brand.md` și de la postările pe care i le dă utilizatorul |
| „AirTime check” | AirTime instalat | chemi skill-ul AirTime cu `args="AirTime check"` |

Dacă nu e instalată niciuna dintre unelte, sari peste întrebare și spui într-un rând ce lipsește și că se instalează din nou cu `setup-mac.sh`.

Înainte de bifele alese, adaugi `"setari": "propuse"` în `onboarding.json`, păstrând restul cheilor. Apoi faci bifele, în ordinea din tabel. La final scrii un rezumat de 2–3 rânduri: ce s-a salvat și unde, ce a rămas de setat.

## Ce nu faci

- Nu ceri parole, chei sau tokeni. Conectările le face utilizatorul în paginile oficiale sau prin scripturile AirTime.
- Nu scrii în afara fișierelor din tabelul de sus.
- Nu repeți întrebarea despre brand după un refuz, decât dacă utilizatorul cere onboarding-ul.

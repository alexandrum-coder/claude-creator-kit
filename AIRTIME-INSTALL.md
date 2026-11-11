# AirTime: instalare și conectare

AirTime ia un singur clip filmat de tine și propune un montaj, un video YouTube programat și 3-5 reels Instagram programate. Ghidul de față te duce prin instalare și prin cele două conectări, o singură dată. Se scrie pentru un MacBook și nu cere cunoștințe tehnice.

**Cum citești ghidul**
- La fiecare pas găsești: contul de care ai nevoie, cât durează și cum verifici că a mers.
- **(UNVERIFIED — butoanele pot avea alt nume)** înseamnă că numele butonului sau al meniului vine din documentația platformei, nu dintr-un ecran văzut la scrierea ghidului. Google, Instagram și Meta își schimbă des paginile. Dacă un buton are alt nume, caută unul asemănător sau cere-i ajutorul lui Claude: „AirTime conectare”.
- Dacă o verificare nu trece, mergi la [Probleme și soluții](#probleme).

**Ordinea:** [instalarea](#instalare) → [YouTube](#youtube) → [Instagram](#instagram) → [Facebook](#facebook) (opțional) → [verificarea finală](#verificarea-finala).

---

<a id="instalare"></a>

## Instalarea dintr-o comandă

- **Cont necesar:** niciunul.
- **Durată:** cam 10-20 de minute, în funcție de internet. Se descarcă mai multe programe.
- **Ce faci:** deschide aplicația **Terminal** (Cmd+Space, scrie „Terminal”, Enter), lipește comanda de mai jos și apasă Enter:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/alexandrum-coder/claude-creator-kit/main/setup-mac.sh)" -- --doar "<N>"
```

`<N>` este numărul din lista scriptului la care apare „airtime”. Scriptul îl alege împreună cu tot ce are nevoie.

- **Cum verifici:** la final scriptul spune că AirTime e instalat. Poți rula și verificarea din [Verificarea finală](#verificarea-finala).

<a id="unelte"></a>

## Ce instalează scriptul

Nu trebuie să instalezi nimic de mână. Scriptul pune pe Mac:

- **Programe de bază:** `node` (rulează șablonul de intro) și `ffmpeg` (taie și îmbină video). Sunt programe gratuite, fără ele nu se poate face montajul.
- **Pluginurile de care depinde AirTime:** `creator-skills`, `ecc`, `marketing`, `brand-voice`, `remotion-skills` și `claude-shorts`. Primele sunt colecții de reguli și unelte pentru Claude; `claude-shorts` taie reels-urile și pune subtitrări.
- **Un mediu separat pentru AirTime**, în `~/.airtime/venv`: biblioteci care vorbesc cu YouTube. Nu atinge restul Mac-ului.
- **Șablonul de intro**, în `~/.airtime/remotion`: se instalează o singură dată.
- **browser-harness:** unealta de rezervă pentru browser (vezi [Rezerva browser](#rezerva-browser)). Se instalează, dar nu se pornește.

**Cum verifici:** spune „AirTime check”. Fiecare unealtă primește ✔ sau ✘. La ✘ vezi motivul. Soluția obișnuită este să rulezi din nou comanda de instalare: ea completează doar ce lipsește.

Dacă la „AirTime check” apare un ✘ cu trimitere la această secțiune și rularea din nou nu ajută, vezi [Probleme și soluții](#probleme).

---

<a id="youtube"></a>

## Conectarea la YouTube

- **Cont necesar:** contul Google cu care ești proprietarul canalului tău YouTube.
- **Durată:** cam 20 de minute, o singură dată.
- **De ce atâția pași:** pentru ca AirTime să programeze videoclipuri pe canalul tău, Google cere să creezi „o cheie” personală, doar a ta. Nu plătești nimic. Google numește asta „proiect” și „aplicație”, dar este doar cheia ta de acces; nu publici nicio aplicație pentru public.

**Pornește conectarea:** spune în Claude „AirTime conectare”. Claude pornește scriptul de conectare pentru tine. Scriptul deschide singur, pe rând, patru pagini Google. La fiecare face ce scrie mai jos, apoi revii în Terminal și apeși **Enter**.

**Pasul 1: proiect nou** (se deschide `console.cloud.google.com/projectcreate`)
1. Dacă te întreabă, intră cu contul Google al canalului.
2. La „Project name” scrie `AirTime`.
3. Apasă **Create**. Așteaptă câteva secunde până apare confirmarea. **(UNVERIFIED — butoanele pot avea alt nume)**
4. Dacă Google cere să accepți termenii, citește-i și acceptă-i tu.

**Pasul 2: activarea YouTube** (se deschide pagina „YouTube Data API v3”)
1. Asigură-te că sus, lângă sigla Google Cloud, este selectat proiectul `AirTime`.
2. Apasă **Enable**. **(UNVERIFIED — butoanele pot avea alt nume)**
3. Pagina se schimbă și arată „API enabled” sau o pagină de administrare a API-ului. Asta înseamnă că a mers.

**Pasul 3: ecranul de consimțământ** (se deschide „OAuth consent screen”). Aici Google te întreabă cine ești și cine are voie să folosească cheia.
1. La „User type” alege **External**, apoi **Create**. **(UNVERIFIED — butoanele pot avea alt nume)**
2. Completează numele aplicației (`AirTime`) și adresa ta de e-mail, atât la „User support email”, cât și la „Developer contact”. Apoi mergi mai departe cu **Save and continue** până la sfârșit. Nu trebuie să adaugi nimic la „Scopes”.
3. Adaugă-te ca **Test user**: la „Test users” apasă **Add users** și scrie adresa contului Google al canalului. **(UNVERIFIED — butoanele pot avea alt nume)**
4. **Pas important: treci aplicația din „Testing” în „In production”.** Pe pagina de consimțământ apasă **Publish app** și confirmă. Pe ecran trebuie să apară starea **In production**. **(UNVERIFIED — butoanele pot avea alt nume)**
   - **De ce:** cât timp aplicația rămâne în „Testing”, Google șterge accesul după 7 zile și AirTime nu mai poate programa. În „In production” accesul rămâne. Nu publici nimic pentru alți oameni: aplicația rămâne doar a ta.
   - Dacă Google cere „verificare” sau trimite la un formular pentru verificarea aplicației, nu o cere: aplicația ta este pentru un singur utilizator, tu.

**Pasul 4: cheia (Desktop app)** (se deschide „Credentials”)
1. Apasă **Create credentials**, apoi **OAuth client ID**. **(UNVERIFIED — butoanele pot avea alt nume)**
2. La „Application type” alege **Desktop app**. Numele poate rămâne cel implicit. Apasă **Create**.
3. În fereastra care apare, apasă **Download JSON**. Fișierul se salvează în **Descărcări** (Downloads) și are un nume care începe cu `client_secret_`.
4. Nu face nimic cu el. Scriptul îl caută singur în Descărcări, cam 10 minute, și îl mută în `~/.airtime` (un folder ascuns, doar al tău). Dacă nu îl găsește în 10 minute, rulează scriptul din nou după ce l-ai descărcat.
5. Nu trimite fișierul nimănui și nu îl pune în e-mail sau pe un drive. Este cheia ta.

**Autorizarea (ultimul pas)**
1. Scriptul deschide o pagină Google de autorizare. Alege contul Google al canalului. Dacă ai mai multe canale, alege-l pe cel pe care vrei să programezi.
2. Google poate arăta ecranul **„Google hasn't verified this app”** („Google nu a verificat această aplicație”). Este normal: aplicația este a ta, nu a trecut printr-o verificare Google, pentru că nu are nevoie de ea. Apasă **Advanced**, apoi **Go to AirTime (unsafe)** („Go to …”, cu numele aplicației tale). **(UNVERIFIED — butoanele pot avea alt nume)**
3. Pe ecranul următor Google listează ce primește AirTime (să urce videoclipuri și să le gestioneze pe canalul tău). Bifează tot ce este cerut și apasă **Continue** sau **Allow**. **(UNVERIFIED — butoanele pot avea alt nume)**
4. Pagina spune că poți închide fereastra. Întoarce-te în Terminal.

**Cum verifici:** scriptul afișează **numele canalului tău**, de exemplu `{"channel": "Numele canalului"}`. Mai târziu, „AirTime check” arată „✔ YouTube (canal …)”. Dacă apare alt canal decât cel dorit, rulează din nou conectarea și alege canalul corect la autorizare.

Dacă pică, vezi [Probleme și soluții](#probleme): „Tokenul a expirat după 7 zile” și „quotaExceeded”.

---

<a id="instagram"></a>

## Conectarea la Instagram

- **Conturi necesare:** contul tău Instagram și, pentru drumul prin Facebook, contul tău Facebook.
- **Durată:** cam 10 minute, o singură dată.
- **Cum merge:** AirTime nu se conectează prin „cheie”, ca la YouTube. El deschide Business Suite (instrumentul oficial Meta pentru programarea postărilor) în browserul tău Chrome, unde ești deja logat, și programează acolo reels-urile. Pentru asta are nevoie de trei lucruri: un cont Instagram profesional, extensia Claude in Chrome și un login în Business Suite.

### Pasul 1: cont profesional de tip Creator

Dacă contul tău este deja „Creator” (Profil → Setări → Tip de cont arată „Creator”), sari la Pasul 2.

1. Deschide aplicația **Instagram** pe telefon și intră în contul tău.
2. Mergi pe profil, apasă meniul (cele trei linii) → **Setări și activitate** (Settings and activity). **(UNVERIFIED — butoanele pot avea alt nume)**
3. Caută **Tip de cont și instrumente** (Account type and tools). Apasă **Treci la cont profesional** (Switch to professional account). **(UNVERIFIED — butoanele pot avea alt nume)**
4. Alege categoria care te descrie (de exemplu „Antrenor” sau „Sport și recreere”) și apasă **Gata**. **(UNVERIFIED — butoanele pot avea alt nume)**
5. La tipul de cont alege **Creator** (nu „Business”). **(UNVERIFIED — butoanele pot avea alt nume)**
6. Dacă aplicația te întreabă dacă vrei să legi o Pagină de Facebook, poți sări peste acest pas acum; îl faci mai jos, la [Facebook](#facebook), dacă vrei.

**Cum verifici:** pe profil, sub nume, apare butonul **Panou profesional** (Professional dashboard). **(UNVERIFIED — butoanele pot avea alt nume)**

### Pasul 2: extensia Claude in Chrome

- **Cont necesar:** contul tău Claude.

1. Deschide browserul **Google Chrome** (nu Safari).
2. Caută în Chrome Web Store „Claude in Chrome” și apasă **Add to Chrome**, apoi **Add extension**. **(UNVERIFIED — butoanele pot avea alt nume)**
3. Apasă iconița de puzzle din dreapta sus și fixează extensia (pinul de lângă ea), ca să o vezi mereu.
4. Deschide extensia și loghează-te cu contul tău Claude.

**Cum verifici:** când ceri „AirTime check”, Claude poate deschide o filă în Chrome. Dacă nu, vezi „Extensia Chrome nu e conectată” în [Probleme și soluții](#probleme).

### Pasul 3: Business Suite, cu două drumuri

Deschide în Chrome `https://business.facebook.com/latest/home`. Dacă cere login, alege drumul care îți merge. Nu spune parola în conversație: o scrii tu, în pagină.

**Drumul A: login cu Instagram (preferat)**
1. Pe pagina de login caută **Continuă cu Instagram** (Log in with Instagram) și apasă. **(UNVERIFIED — butoanele pot avea alt nume)**
2. Scrie numele de utilizator și parola Instagram și confirmă codul de securitate dacă îl cere.
3. Acceptă legarea contului.

**Drumul B: login cu Facebook (dacă A nu merge)**
1. Pe pagina de login alege **Continuă cu Facebook** (Log in with Facebook) și intră cu contul tău Facebook. **(UNVERIFIED — butoanele pot avea alt nume)**
2. Dacă Business Suite nu arată contul Instagram, leagă-l: **Setări** → **Conturi Instagram** → **Conectează contul** (Settings → Instagram accounts → Connect account). **(UNVERIFIED — butoanele pot avea alt nume)**
3. Pentru Facebook, legarea Paginii se face la [Facebook](#facebook).

**Cum verifici (drumul A sau B):** pagina **Acasă / Home** din Business Suite se deschide și arată numele contului tău Instagram în selectorul de conturi, sus sau în stânga.

### Verificarea: „AirTime check”

Spune „AirTime check”. Claude deschide Business Suite și confirmă două lucruri: că vede contul tău și că vede butonul de reel. De asemenea notează în profil care drum de login a mers (Instagram sau Facebook). Textele reale ale butoanelor se notează la această verificare, nu aici.

**Dacă nu merge:** vezi „Business Suite nu arată contul” și „Butonul de reel lipsește” în [Probleme și soluții](#probleme).

---

<a id="facebook"></a>

## Facebook, opțional

- **Cont necesar:** contul tău Facebook, administrator al unei Pagini de Facebook. AirTime poate pune reels-urile și pe Pagină. Fără acest pas, merg doar pe Instagram.
- **Durată:** cam 5 minute.

1. Deschide Business Suite (`business.facebook.com`), logat cu Facebook (drumul B de mai sus).
2. Mergi la **Setări** → **Pagini** (Settings → Pages) și verifică dacă Pagina ta apare. Dacă nu apare, apasă **Adaugă Pagină** (Add Page) și alege-o pe a ta. **(UNVERIFIED — butoanele pot avea alt nume)**
3. Dacă vrei ca reels-urile să meargă și pe Pagină, la același loc alege să legi contul Instagram de Pagină. **(UNVERIFIED — butoanele pot avea alt nume)**

**Cum verifici:** spune „AirTime check”. Pagina ta trebuie să apară în listă, lângă contul Instagram. Dacă lipsește, Claude programează doar pe Instagram și îți spune în raport că Facebook nu a mers.

---

<a id="rezerva-browser"></a>

## Rezerva pentru browser: browser-harness

- **Cont necesar:** niciunul în plus.
- **Durată:** 2 minute, o singură dată.
- **Când se folosește:** numai când extensia Claude in Chrome nu reușește un pas în Business Suite. Atunci AirTime încearcă o singură dată cu browser-harness. Dacă nu îți e nevoie, nu activa nimic.

**Cum o activezi**
1. În Chrome, scrie în bara de adrese `chrome://inspect/#remote-debugging` și apasă Enter.
2. Pornește opțiunea de depanare la distanță (remote debugging), așa cum o arată pagina. **(UNVERIFIED — butoanele pot avea alt nume)**

**Ce expune, pe înțelesul tuturor.** Cât timp opțiunea este pornită, orice program de pe Mac-ul tău poate controla Chrome-ul în care ești logat: poate citi ce vezi, poate apăsa pe butoane în numele tău, inclusiv în conturile în care ești intrat (Instagram, Facebook, banca, e-mailul). Folosește-o doar cât ai nevoie și numai pe un Mac pe care nu rulează programe pe care nu le cunoști.

**Cum o oprești**
1. Reîntoarce-te la `chrome://inspect/#remote-debugging` și oprește opțiunea. **(UNVERIFIED — butoanele pot avea alt nume)**
2. Închide complet Chrome (Cmd+Q) și deschide-l din nou.

**Cum verifici:** „AirTime check” spune dacă rezerva e pregătită. Dacă nu ai pornit-o, e în regulă: nu e obligatorie.

---

## Plan B: Composio (numai ca rezervă, de verificat prețul)

Composio este un serviciu extern care se poate conecta la YouTube și Instagram în locul conexiunii de mai sus. **Nu este varianta principală.** Se folosește numai când conexiunea principală nu merge. Limitele lui:

- **Instagram:** Composio publică numai pe loc, fără programare. Pentru programare rămâne Business Suite.
- **Cont propriu:** ai nevoie de un cont Composio al tău.
- **Date la un terț:** fișierele și tokenurile (cheile de acces) trec prin serviciul Composio, nu rămân doar pe Mac-ul tău.
- **Preț și limite ale planului gratuit: de verificat prețul** înainte să-l folosești. UNVERIFIED.

Dacă nu ai un motiv clar, rămâi la conexiunile din ghid.

---

<a id="verificarea-finala"></a>

## Verificarea finală

1. **„AirTime check”**, spus în Claude. Verifică uneltele, YouTube și Business Suite. Cu testul de viteză, îți spune și cât durează transcrierea unui clip de 20 de minute pe Mac-ul tău. Tot ce e obligatoriu trebuie să aibă ✔.
2. **Verificarea generală**, în Terminal:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/alexandrum-coder/claude-creator-kit/main/setup-mac.sh)" -- --check
```

Unealta AirTime trebuie să aibă ✔, cu dependențele și cele două conexiuni.

**Gata când:** vezi ✔ la YouTube (cu numele canalului tău), ✔ la uneltele de bază, iar Business Suite arată contul tău Instagram.

---

<a id="probleme"></a>

## Probleme și soluții

**1. Tokenul a expirat după 7 zile (YouTube nu mai merge)**
- **Cauză:** aplicația Google a rămas în „Testing”. Google șterge accesul după 7 zile.
- **Soluție:** deschide pagina „OAuth consent screen” din Google Cloud și verifică starea. Dacă scrie „Testing”, apasă **Publish app** până scrie **In production**. **(UNVERIFIED — butoanele pot avea alt nume)** Apoi spune din nou „AirTime conectare” ca să primești un acces nou.

**2. `quotaExceeded` (Google spune că ai depășit limita zilei)**
- **Cauză:** YouTube dă, pe zi, un număr limitat de operațiuni pentru contul gratuit, iar un videoclip urcat consumă mult din ele.
- **Soluție:** nu repeta urcarea. Așteaptă până a doua zi (limita se resetează la miezul nopții, ora Pacificului) și reia. Dacă primești des eroarea, cere în Google Cloud o limită mai mare (pagina „Quotas” a API-ului YouTube). **(UNVERIFIED — butoanele pot avea alt nume)**

**3. Videoclipul a rămas privat sau a fost blocat**
- **Cauză:** privat este normal înainte de ora programată: YouTube îl face public la momentul stabilit. Blocat înseamnă că YouTube l-a marcat (de obicei din cauza muzicii cu drepturi de autor).
- **Soluție:** deschide YouTube Studio → Conținut și vezi mesajul de lângă videoclip. Pentru „privat”: verifică la „Vizibilitate” că ora programată este cea dorită. Pentru „blocat”: înlocuiește muzica sau contestă din Studio. Spune „AirTime check” după ce rezolvi. AirTime verifică la Google că videoclipul a rămas programat; dacă raportul spune altceva, nu urca a doua oară de mână, ci cere ajutorul lui Claude.

**4. Business Suite nu arată contul**
- **Cauză:** contul Instagram nu este legat, sau ești logat cu alt drum (Instagram față de Facebook).
- **Soluție:** în Business Suite, **Setări** → **Conturi Instagram** → **Conectează contul**. **(UNVERIFIED — butoanele pot avea alt nume)** Dacă tot nu apare, încearcă celălalt drum de login (A sau B) din [Instagram](#instagram). Verifică și că contul este profesional.

**5. Butonul de reel lipsește**
- **Cauză:** contul nu este profesional, sau Meta a schimbat numele butonului.
- **Soluție:** verifică în aplicația Instagram că tipul contului este Creator (Pasul 1). Apoi spune „AirTime check”: Claude citește textele reale din Business Suite și le notează. Dacă tot lipsește, programează reelul de mână (Claude îți pregătește fișierul, descrierea și ora într-un fișier `manual.md`).

**6. Extensia Chrome nu e conectată**
- **Cauză:** extensia nu e instalată în Chrome, nu e logată sau Chrome nu e deschis.
- **Soluție:** deschide Chrome, apasă iconița extensiei Claude in Chrome și loghează-te. Dacă iconița lipsește, reinstalează-o din Chrome Web Store. Nu merge în Safari. Dacă tot nu merge, folosește [rezerva browser](#rezerva-browser).

**7. Transcrierea e prea lentă**
- **Cauză:** Mac-ul este mai vechi sau prea ocupat.
- **Soluție:** închide celelalte programe mari și lasă Mac-ul conectat la priză. Rulează „AirTime check” cu testul de viteză: îți spune cât ar dura un clip de 20 de minute și alege singur un model mai mic de transcriere. Pentru clipuri foarte lungi, taie-le în două înainte.

**8. `ffmpeg` lipsește**
- **Cauză:** programul de montaj nu s-a instalat.
- **Soluție:** rulează din nou comanda din [Instalarea dintr-o comandă](#instalare). Ea completează numai ce lipsește. Dacă mesajul revine, cere ajutorul lui Claude; nu instala de mână programe necunoscute.

**9. Fișierul de la Google nu e găsit (scriptul spune „Nu am găsit fișierul în 10 minute”)**
- **Cauză:** `client_secret_….json` nu e în Descărcări, sau browserul l-a salvat în alt loc.
- **Soluție:** descarcă din nou fișierul (Pasul 4 la YouTube) și mută-l în Descărcări, apoi rulează scriptul din nou.

**10. Ecranul „Google hasn't verified this app” nu are butonul de continuare**
- **Cauză:** adresa ta nu e trecută ca Test user, sau aplicația nu e publicată.
- **Soluție:** la Pasul 3 adaugă-ți adresa la „Test users” și apasă **Publish app**. Apoi reia autorizarea. **(UNVERIFIED — butoanele pot avea alt nume)**

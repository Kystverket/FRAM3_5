

==========================
FRAM 3
==========================

.. image:: https://github.com/kystverket/FRAM/workflows/Pytest/badge.svg
   :scale: 100 %
   :alt: Build Status


FRAM 3 er kystverkets modell for samfunnsøkonomisk analyse av farledstiltak.

Modellen beregner følgende virkninger:

- Distanseavhengige kostnader
- Tidsavhengige kostnader
- Lokale utslipp til luft (PM10 og NOX)
- Globale utslipp til luft (CO2)
- Oppgraderings- og vedlikeholdskostnader av merker
- Investeringskostnader inkludert CO2-utslipp i anleggsfasen
- Skattefinansieringskostnader
- Ulykkeskostnader ved grunnstøting, kontatkskade og kollisjoner:
    - Reparasjonskostnader som følge av materielle skader
    - Tid ute av drift som følge av materielle skader
    - Personskader
    - Dødsfall
    - Utslipp av olje og opprenskingskostnader
- Nytte ved opprensking av forurensede sedimenter

Du kan lese mer om modellen, hvordan den settes opp, hvordan den brukes og om de ulike virkningene på tinyurl.com/framdokumentasjon.

Innhold i denne guiden
--------------------------
 - `Oppstart`_
    - `Installasjon av modellen`_
    - `Oppsett av kodemiljø`_
 - `Bruk av kjor-fram-scriptet`_
 - `Bruk i Python`_
 - `Input til modellen`_
    - `Ark i inputfila`_
    - `Forutsetninger`_
    - `Innlesing av risikoanalyser`_
    - `Konsekvensreduserende tiltak`_
    - `Følsomhetsanalyser`_
 - `Output og informasjon som ligger på FRAM`_
 - `Valideringer`_

Oppstart
------------


Installasjon av modellen
~~~~~~~~~~~~~~~~~~~~~~~~

FRAM 3 kan installeres med pip fra git. Pip funker med conda og kan installeres med ``conda install pip``. Selve installasjonen fra github kan ta litt tid, så ikke avbryt hvis den ser ut som den står og henger i noen minutter.

Du installerer modellen fra terminalen der du kjører Python-kode fra. Det kan for eksempel være i en jupyter notebook, i en powershell-terminal, i en conda-terminal eller annet.

.. code-block:: bash

    pip install git+https://github.com/Kystverket/FRAM

Eller hvis du vil ha koden lett tilgjengelig, og ikke gjemt bort i en pip-mappe kan du klone den ned fra git. Det krever at du har installert ``git`` fra før. Før du kloner ned fra git må du stå i den mappen der du ønsker
at koden skal lastes ned. Du kan sjekke hvilken mappe du står i ved å skrive pwd i din terminal. Når du kjører koden under vil det lages en mappe her som heter FRAM.

.. code-block:: bash
    git clone https://github.com/Kystverket/FRAM fram
    cd fram
    python setup.py install


Det er to måter å kjøre FRAM3 på: Gjennom ``kjor-fram``-kommandoen, eller ved å importere ``fram``-pakken i python.
FRAM krever Python >=3.10 for å kjøre.

Oppsett av kodemiljø
~~~~~~~~~~~~~~~~~~~~
Det anbefales alltid å bruke kodemiljøer til å begrense skopet til installerte pakker.

Det finnes mange måter å løse dette på (virtual environments og Docker er to alternativer).
FRAM kommer med to sett pakker som er nødvendige. `requirements.txt` inneholder de pakkene man behøver for
å kjøre modellen, her er alle versjoner av pakkene låst. `requirements-dev.txt` inneholder i tillegg de pakkene
som benyttes for å utvikle modellen (testing, bygge dokumentasjon m.m.).

Disse kan installeres med hhv `pip install -r requirements.txt` og `pip install -r requirements-dev.txt`.
Det krever at du står i mappen der requirementsfilen ligger, enten i fram-mappen du fikk da du klonet den ned eller i pip-mappen hvis du installerte modellen.
Alternativt kan du også laste ned requirements-filen fra github.com, og legge denne et sted lokalt på PCen din.




Bruk av kjor-fram-scriptet
---------------------------
Når du installerer FRAM gjennom pip så installeres det automatisk en kommando for kjøring av modellen som kan kjøres hvor som helst. For å kjøre modellen må du også oppgi verdier til nøkkelordene ``--filbane``, ``--tiltakspakke`` og ``--ra_dir`` som angir hhv. filbane til inputfil, tiltakspakke og filbane til mappen med risikoanalyser. For eksempel kjører en eksempelkjøring fra eksempelmappen på git med koden under:

.. code-block:: bash

    kjor-fram --filbane="Inputfiler/Strekning 10.xlsx" --tiltakspakke=1 --ra-dir="RA"



I tillegg til ``--filbane``, ``--tiltakspakke`` og ``--ra-dir`` så kan man oppgi følgende nøkkelord:

- --``sammenstillingsaar``:
    Int, det året vi diskonterer til. Default er sammenstillingsåret
    spesifisert i Forutsetninger_FRAM.xlsx som ligger på fram. Dersom verdi i initalisering vil denne overskrive det som ligger i excelfilen.
- --``ferdigstillelsesår``:
    Int, åpningsåret, det året tiltakene er ferdigstilt,
    og derfor det året vi teller nytte fra. Default er forutsetning
    spesifisert i Forutsetninger_FRAM.xlsx som ligger på fram. Dersom verdi i initalisering vil denne overskrive det som ligger i excelfilen.
- --``analysepeperiode``:
    Int, antall år vi teller nytte for. Default er forutsetning
    spesifisert i Forutsetninger_FRAM.xlsx som ligger på fram.
- --``levetid``:
    Int, antall år vi teller nytte for over levetiden. Default er forutsetning
    spesifisert i Forutsetninger_FRAM.xlsx som ligger på fram.
- --``trafikkgrunnlagsaar``:
    Int, det året trafikktellingene er basert på. Default er 2019.
- --``andre_skip_til_null``:
    Bool, hvorvidt vi nuller alle skip i skipstypen 'Annet'. Default er
    true.
- --``delvis_fram``:
    Hvorvidt det er meningen, og dermed tillatt, å kjøre en FRAM uten at det defineres trafikk, tidsavhengige,
    distanseavhengige og risiko
- --``logging_level``:
    Justerer hvor mye output du vil ha fra prosessen. Ved vanlig drift
    er 'INFO' ok. Mulige verdier er 'DEBUG', 'INFO', 'WARNING', 'ERROR', og 'CRITICAL'
- --``les_RA_paa_nytt``:
    Hvorvidt IWRAP-RA skal tvangsleses fra underliggende excel-filer, default er False
- --``aisyrisk_input``:
    Hvorvidt AISyRISK er benyttet som risikomodell. Default er False.
- --``folsomhetsanalyser``:
    Hvorvidt følsomhetsanalyser skal kjøres. Kan også være en liste med egendefinerte faktorer som skal ganges
    inn i input for hver virkning, eller en dict med analysenavn som nøkler og en dict med variabelnavn som
    nøkler og faktorer som verdier som verdier.
    Standard hvis True oppgis med hhv. 0.8 og 1.2 for alle variabler.


Bruk i Python
-------------
FRAM3 kan importeres til python og brukes i scripts, notebooks eller pakker. Bruken foregår hovedsakelig i to enkle steg: Initialisering og kjøring.
Dersom du ønsker å bruke modellen i jupyter notebook må du installere jupyter i samme miljø som modellen ble installert.

Først må modellen intialiseres med alle forutsetninger for analysen.
Initialiseringen baseres på en Excel-fil med én eller flere tiltakspakker
(typisk en strekning). Når objektet er initialisert så kan den kjøres på én
og én tiltakspakke med funksjonen :py:meth:`~fram.modell.FRAM.run`.

Kodesnutten under viser kode for importering og kjøring av en
eksempelstrekning inkludert i kodebasen. Hvis du skal kjøre snutten må ``FRAM_DIRECTORY`` peke til mappen der du har klonet ned git-repoet.

.. code-block:: python

    from fram import FRAM
    from pathlib import Path
    FRAM_DIRECTORY = Path("./fram/")

    fram_modell = FRAM(
        FRAM_DIRECTORY / "eksempler" / "eksempel_analyser" / "Inputfiler" / "strekning 11.xlsx",
        tiltakspakke=11,
        ra_dir=FRAM_DIRECTORY / "eksempler" / "risikoanalyser"
    )

    fram_modell.run()

I kodesnutten over kjøres en eksempelfil som ligger i FRAM_DIRECTORY, men input trenger ikke ligge i noen spesifikk mappe, så lenge du peker til den når du initialiserer modellen. Se nærmere forklaring i `Andre parametre`_.


Modellen tar følgende parametre ved initialisering:

.. code-block:: python

    fram_modell = (
        strekning=None,
        tiltakspakke=1,
        sammenstillingsaar=None,
        ferdigstillelsesaar=None,
        analyseperiode=None,
        trafikkgrunnlagsaar=2019,
        levetid=None,
        andre_skip_til_null=True,
        beregn_oljeutslipp=False,
        logging_level="DEBUG",
        ra_dir=None,
        les_RA_paa_nytt=False,
    )

- strekning:
    En streng eller en filbane. Strenger konverteres til filbaner. Den forventer
    at filen den finner der, følger formateringsreglene. Husk at filen må ha samme navn
    som strekningen spesifisert i excelarket.
- tiltakspakke:
    Int, hvilken tiltakspakke (fane i input-arket) vi skal beregne
    effekter på. Default er 1.
- sammenstillingsaar:
    Int, det året vi diskonterer til. Default er sammenstillingsåret
    spesifisert i Forutsetninger_FRAM.xlsx som ligger på fram.
- ferdigstillelsesår:
    Int, åpningsåret, det året tiltakene er ferdigstilt,
    og derfor det året vi teller nytte fra. Default er forutsetning
    spesifisert i Forutsetninger_FRAM.xlsx som ligger på fram
- analysepeperiode:
    Int, antall år vi teller nytte for. Default er forutsetning
    spesifisert i Forutsetninger_FRAM.xlsx som ligger på fram.
- trafikkgrunnlagsaar:
    Int, det året trafikktellingene er basert på. Default er 2019.
- levetid:
    Int, antall år vi teller nytte for over levetiden. Default er forutsetning
    spesifisert i Forutsetninger_FRAM.xlsx som ligger på fram.
- andre_skip_til_null:
    Bool, hvorvidt vi nuller alle skip i skipstypen 'Annet'. Default er
    true.
- delvis_fram:
    Hvorvidt det er meningen, og dermed tillatt, å kjøre en FRAM uten at det defineres trafikk, tidsavhengige, distanseavhengige og risiko
- logging_level:
    Justerer hvor mye output du vil ha fra prosessen. Ved vanlig drift
    er 'INFO' ok. Mulige verdier er 'DEBUG', 'INFO', 'WARNING', 'ERROR', og 'CRITICAL'
- ra_dir:
    pathlib.Path som peker til hvor RA-filene fra IWRAP ligger. Defaulter til banen der Excel-input ligger, og mappen risikoanalyser ved siden av Excel-filen
- les_RA_paa_nytt:
    Hvorvidt IWRAP-RA skal tvangsleses fra underliggende excel-filer, default er False

Input til modellen
------------------

Inputfila kan ligge hvor som helst, og oppgis eksplisitt som argument når
modellen initialiseres. Inputfila inneholder blant annet:

- Definisjoner, navn, og oversikt over strekningen
- Sårbarhet for områder langs strekningen
- Trafikkgrunnlag, -prognoser og -overføring
- Seilingstider
- Investeringskostnader (med eventuelle utslipp i anleggsfasen)
- Miljøforbedrende tiltak (forurensede sedimenter)
- Øvrige kontantstrømmer
- Nye navigasjonsinnretninger
- Parametre for ventetidsberegninger

Eksempel på inputfil kan `lastes ned her <https://github.com/Kystverket/FRAM/raw/FRAM3_4/fram/eksempler/eksempel_analyser/Inputfiler/Strekning%2011.xlsx>`_.


Ark i inputfila
~~~~~~~~~~~~~~~


- Arknavn: Ruteoversikt
           Spesifiser hvilke ruter som inngår på hvert Analyseomraade,
           Tiltakspakke, Tiltaksomraade og Strekning. Alle ruter må ha
           unike navn, og alle analyseområder må ha minst en rute. Tiltaksområde og pakke må være et tall, mens rutene og analyseområdet må være en streng.
- Arknavn: Risikoanalyser referansebanen
           Spesifiserer hvilke risikoanalyser som skal ligge til grunn i
           ra_startaar og ra_fremtidsaar i referansebanen for hver rute som er oppgitt i
           Ruteoversikten. Alle ruter må ha en risikoanalyse i ra_startaar og i ra_fremtidsaar.
           Dersom flere ruter inngår på samme analyseomraade og dermed
           har samme risikoanalyse må navnet likevel spesifiseres på alle rutene.
           Således kan det finnes flere ruter med samme risikoanalyse.
           Modellen er lagt opp slik at når du for første gang leser inn RA
           i din RA-dir, vil det opprettes en .json-fil med alle de relevante
           RA spesifisert i de ulike tiltakspakkearkene og i risikoanalyser
           i referansebanen. Dersom du på et senere tidspunkt legger inn
           flere analyser i inputarket må du slette den eksisterende json-filen
           slik at denne lages på nytt.
- Arknavn: Sarbarhet
           Vurdering av sårbarhetsnivå og lokalisering (fylke) for hvert analyseområde,
           tiltakspakke, tiltaksområde og strekning. Sårbarhet tar fire verdier
           (Liten, Moderat, Hoy, Svaart hoy).
           Fylker tar følgende verdier: Ostfold, Akershus, Oslo, Buskerud, Vestfold,
           Telemark, Aust-Agder, Vest-Agder, Rogaland, Hordaland, Sogn og Fjordane,
           More og Romsdal, Sor-Trondelag, Nord-Trondelag, Nordland, Troms, Finnmark 
- Arknavn: Trafikkgrunnlag
           Antall passeringer for ulike skipstyper, lengdegrupper på hver rute.
           Trenger kun å ta med relevante skipstyper og lengdegrupper. Alle ruter
           må ha trafikkgrunnlag.
- Arknavn: Grunnprognoser
           Kystverkets grunnprognoser for anløp til norske havner fra 2018. Må
           spesifiseres for alle skipstyper og lengdegrupper som inngår i
           trafikkgrunnlaget.
- Arknavn: Prognoser justert
           Justering av prognoser for skipstyper lengdegrupper som skal ha
           justerte prognoser på rutenivå. Justeringen som legges inn er
           "nye" prognoser - altså at prognosen fra Kystverkets offisielle
           prognoser ersattes av det som spesifiseres.
- Arknavn: Seilingstid
           Seilingstid for hver rute. Trenger kun å spesifisere opp seilingstid
           for de rutene, skipstypene og lengdegruppene der man forventer
           virkninger for en av tiltakspakkene på strekningen. Dersom alle
           skipstyper og eller lengdegrupper har samme seilinsgtid og fart kan
           man i kolonnene "Skipstype" og/eller 'Lengdegruppe' skrive "Alle".
           Da vil alle skip (enten innenfor samme skipstype og/eller samme
           lengdegruppe) få samme seilingstid i referansebanen. Tidsbruk skal oppgis
           i timer og Hastighet i knop.
- Arknavn: Investeringskostnader
           For hver tiltakspakke må det spesifiseres investeringskostnader.
           Forventningsverdi og P50. Hvis du ikke har P50 trenger denne ikke
           spesifiseres da dette kun er med for å kjøre følsomhetsanalyser. Det
           må også spesifiseres hvilken kroneverdi investeringskostnadene er oppgitt
           i samt første år med kostnader (fra og med) og siste år med kostnader
           (til og med) eller en kolonne med "Anleggsperiode". Husk at ferdigstillelsesår minus Anleggsperiode
           ikke må være mindre enn analysestart, altså bakoverskuende. Det kan også angis CO2-utslipp i anleggsfasen
           i kolonnen "tonn CO2 anleggsfasen", dersom anleggsperioden vil føre med seg CO2-utslipp.
- Arknavn: Forurensede sedimenter
           For hver tiltakspakke og hvert tiltaksområde det forurensede sedimenter er relevant må det
           spesifiseres endringen i disse sedimentene. Man må fylle ut informasjon om tilstandsendringen som
           følge av tiltaket, hvilken kommune tiltaket befinner seg i og hvor stort areal tiltaksområdet
           utgjør.
- Arknavn: Tiltakspakke XX
   Må spesifiseres for hver tiltakspakke der XX tilsvarer "Tiltakspakke"
   i øvrige arkfaner. I dette arket må følgende spesifiseres:

    - TRAFIKKOVERFØRING
         Ved trafikkoverføring må man spesifisere hvilke rute trafikkoverføringen
         tas fra og hvilken rute skipene overføres til. Det trengs kun å
         spesifiseres for de skipstypene og lengdegruppene der man forventer
         trafikkoverføringself. Videre må man spesifisere hvor stor andel
         av trafikken innenfor riktig skipstype/lengdegruppe på "fra ruten"
         som forventes overført. og når man forventer at overføringen vil
         ferdigstilles. I modellen antar vi lineær opptrapping av overføringen
         fra og med ferdigstillesår og til og med "Overfort_innen".

    - BRUTTO SEILINGSTID TILTAKSBANEN
            Ny seilingstid og hastighet i tiltaksbanen må spesifiseres for de
            skipstyper og lengdegrupper på hver rute der man forventer endring
            i disse parameterene fra referansebanen. Seilingstid må oppgis i
            brutto seilingstid timer, og hastighet i brutto hastighet i knop.

    - RISIKOANALYSER
            For hver risikoanalyse i referansebanen (både i ra_startaar og i ra_fremtidsaar) må
            man spesifisere hvilke risikoanalyse som vil være gjeldende i
            tiltaksbanen. NB!! Husk at dette må gjøres for begge risikoårene -
            altså ra_startaar og ra_fremtidsaar.  Dersom det er kjørt RA på trafikk i tiltaksbanen
            som avviker fra trafikken i referansebanen (hovedsakelig relevant
            ved trafikkoverføring) må dette spesifisers med "Tiltak". Dersom RA
            er kjørt med samme trafikkgrunnlag som i referansebanen må dette
            spesifisres med "Referanse". NB!!! Husk at dette gjelder spesifisering
            av hvilket trafikkgrunlag som har inngått i risikoanalysen.

    - VEDLIKEHOLDSKOSTNADER
            For hvert tiltakspunkt og tiltakspakke spesifiser hvilke objekttype
            man fjerner  og hvilke objekttyper som legges til (+). Hånderer
            kun objekttypene spesifisert i arkfanen "Listevalg"

    - KONSEKVENSREDUSERENDE TILTAK
            Dersom man analyserer tiltak som reduserer utslippskonsekvenser, må
            man først finne ut av hvilke analyseområder man vil endre utslippskonsekvensene
            for, og om man vil endre for referanse, tiltak eller begge.
            For hvert analyseområde og hver ref/tiltak man vil endre,
            må man i input-boken legge inn fullverdige utslippskonsekvensark på nøyaktig
            samme format som arket `konsekvenser_utslipp` i booken `Forutsetninger_SOA.xlsx`.
            For at FRAM skal finne disse, må arknavnene angis i kolonne AR:AT
            i arket for den aktuelle tiltakspakken. Se eksempel i
            `tests/input/strekning 11-konsekvensreduksjon.xlsx`. For de analyseområdene og
            de ref/tiltaks-banene der brukeren ikke har angitt noe, benyttes standard fra FRAM.


- Arknavn: ventetid_x_referanse og ventetid_x_tiltak
            Dersom det er ventetids- eller køproblematikk på strekningen, kan SØA-modellen beregne
            gevinstene ved tiltak som reduserer disse. Det må i så fall utarbeides et par med ark
            for hvert problemområde. Arket må følge en streng mal, se eksempelinputen.
            I arket må man angi hvilken tiltakspakke området dreier seg om, hvilket analyseområde og
            hvilken rute. Kømodellen håndterer flere løp (for eksempel rundt en holme), også kjent som
            flaskehalser. Den håndterer også trafikk i to ulike retninger.
            Man kan beregne for flere ulike perioder av året, dersom det er sesongvariasjoner i
            trafikken. Videre må man angi hvor ofte skip anløper (i hver retning)
            og hvor stor kapasitet hver flaskehals har.

- Arknavn:  `Konsekvensinput referansebanen` og `Konsekvensinput TP {tiltakspakke}`
            Det er siden `FRAM_cruise` lagt til rette for konsekvensreduserende tiltak. For å kunne gjennomføre slike, må man angi konsekvensmatriser, enten for skade/dødsfall, eller utslipp.

            For skade/dødsfall angis disse i form av konkrete sannsynligheter for hhv dødsfall og skade, og forventet antall dødsfall/skade gitt at
            minst én slik inntreffer. Defaultverdier ligger lagret i `Forutsetninger_SOA.xlsx`, og kan hentes ut ved `~fram.virkninger.risiko.hjelpemoduler.generelle.hent_ut_konsekvensinput`, som tar et valgfritt argument `excel_filbane`, slik at du kan lagre filen til enklere bruk.
            For å vurdere konsekvensreduserende tiltak, må det legges et ark med tilsvarende format i input-boken din. Et ark `Konsekvensinput referansebanen` overstyrer referansebanekonsekvensene, mens et ark `Konsekvensinput TP {tiltakspakke}` overstyrer for tiltakspakken.
            Når det først angis konsekvensmatrise for enten ref eller tiltak, må det angis for alle skip, lengder og ruter. Default-inputen har bare id-kolonnene Skipstype, Lengdegruppe og Hendelse. Dersom man vil differensiere per Analyseomraade eller Rute, kan man legge til
            denne kolonnen, og angi fulle konsekvensinputer for hvert Analyseomraade eller hver Rute. Hvis man ikke angir det ene nivået, antas det at man vil ha like verdier for alle disse. (Hvis man legger inn kolonnen Analyseomraade, med to verdier for de to analyseområdene
            sine, men ikke angir kolonnen Rute, forutsetter FRAM at du vil ha like konsekvenser på alle ruter i hvert analyseområde.)
- Arknavn: Kontantstrømmer
           Arkfane for å legge til virkninger som ikke er en del av standard framanalyse. Dette arket må ha fem kolonner:
           Navn: navn på virkningen.
           Tiltakspakke: tiltakspakkenavn.
           Kroneverdi: Prisår for virkningen.
           Aktør: liste som tar verdiene: "Trafikanter og transportbrukere", "Det offentlige", "Samfunnet for øvrig", "Operatører", 'Ikke kategorisert'
           Andel skattefinanseringskostnad: tar verdi mellom 0 og 1, avhengig av hvor stor andel av virkningen det skal beregnes skattefinanseringskostnader av.
Forutsetninger
~~~~~~~~~~~~~~~
Input til modellen består i hovedsak av to Excel-filer, forutsetninger og
input. Filen med forutsetninger er hardkodet til å ligge i
fram/Forutsetninger_FRAM.xlsx. Forutsetningsfilen inneholder blant annet:

- Årstall som setter tidsrammen for tiltaket
- Fremskrivinger for KPI, BNP, valutakurser og deflatorer
- Tidskostnader
- Drivstoffeffektivisering
- Blokkoeffisient og drivstoffmiks per skipstype
- Drivstoffpriser
- Virkningsgrader og energikonvertering for forskjellige drivstoff
- Befolkning i kommuner
- Konsekvenser av ulykker
- Kalkulasjonspriser for forurensede sedimenter, helseskader, materielle skader, utslipp og vedlikehold av navigasjonsinnretninger.

Forutsetningsfilen kan lastes ned `her <https://github.com/Kystverket/FRAM/raw/FRAM3_4/fram/Forutsetninger_FRAM.xlsx>`_.



Innlesing av risikoanalyser
~~~~~~~~~~~~~~~~~~~~~~~~~~~
I de aller fleste tilfeller, og i alle versjoner av FRAM før 3.5, ble risikoanalysene utført i programmet IWRAP. Fra IWRAP genereres et sett med resultatfiler, som måler frekvenser (absolutt antall hendelser) per år, på rutenivå.
Det genereres frekvenser fra IWRAP for to såkalte RA-år. Disse filene leses så inn i FRAM og omdannes til prognostiserte hendelser for alle analyseårene.
Innlesing skjer ved hjelp av kode i filen `~fram.virkninger.risiko.hjelpemoduler.generelle` og fremskrivingen ved hjelp av `~fram.virkninger.risiko.hjelpemoduler.iwrap_fremskrivinger`.

I FRAM 3.5 introduserte vi muligheten til å også benytte risikoanalyser beregnet i verktøyet AISyRISK. I dette verktøyet genereres det frekvenser kun for ett RA-år. I AISyRISK benyttes en annen kategorisering etter
skipstype og lengdegruppe enn det som gjøres i FRAM og IWRAP. Disse må derfor konverteres for å kunne benyttes inn i FRAM. Konverteringsmatrisene ligger i boken `Forutsetninger_FRAM.xlsx` i fanene
`aisyrisk_skipstypekonvertering` og `aisyrisk_lengdekonvertering`. For å benytte AISyRISK-kjøringer må det angis ved initialisering av FRAM (`aisyrisk_input=True`).
Risikokjøringen leses da inn av kode i filen `~fram.virkninger.risiko.hjelpemoduler.generelle` og konvertering og fremskrivingen skjer ved hjelp av kode i filen
`~fram.virkninger.risiko.hjelpemoduler.aisyrisk`.


**Innlesing av risikoanalyser** er tidkrevende. Siden risikoen er den
samme på tvers av analyser for samme strekning, mellomlagres de innleste
tallene. Neste gang modellen kjøres vil den først se etter de mellomlagrede
tallene, og bruke dem i stedet for å lese inn alt på nytt.

For å unngå dette, og tvinge modellen til å lese inn risikoanalysene fra kilden
kan man sende med les_RA_paa_nytt=True i initialiseringen som vist under:

.. code-block:: python

    fram_modell = FRAM(
        FRAM_DIRECTORY / "eksempler" / "strekning 11.xlsx",
        tiltakspakke=11,
        ra_dir=FRAM_DIRECTORY / "eksempler" / "risikoanalyser",
        les_RA_paa_nytt=True
    )

Det er også mulig å benytte AISyRISK som risikomodell. Dette er utdypet på siden `~fram.virkninger.risiko.virkning`

Konsekvensreduserende tiltak
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Det er siden `FRAM_cruise` lagt til rette for konsekvensreduserende tiltak. For å kunne gjennomføre slike, må man angi konsekvensmatriser. Disse angis i form av konkrete sannsynligheter for hhv dødsfall og skade, og forventet antall dødsfall/skade gitt at
minst én slik inntreffer. Defaultverdier ligger lagret i `Forutsetninger_SOA.xlsx`, og kan hentes ut ved `~fram.virkninger.risiko.hjelpemoduler.generelle.hent_ut_konsekvensinput`, som tar et valgfritt argument `excel_filbane`, slik at du kan lagre filen til enklere bruk.
For å vurdere konsekvensreduserende tiltak, må det legges et ark med tilsvarende format i input-boken din. Et ark `Konsekvensinput referansebanen` overstyrer referansebanekonsekvensene, mens et ark `Konsekvensinput TP {tiltakspakke}` overstyrer for tiltakspakken.
Når det først angis konsekvensmatrise for enten ref eller tiltak, må det angis for alle skip, lengder og ruter. Default-inputen har bare id-kolonnene Skipstype, Lengdegruppe og Hendelse. Dersom man vil differensiere per Analyseomraade eller Rute, kan man legge til
denne kolonnen, og angi fulle konsekvensinputer for hvert Analyseomraade eller hver Rute. Hvis man ikke angir det ene nivået, antas det at man vil ha like verdier for alle disse. (Hvis man legger inn kolonnen Analyseomraade, med to verdier for de to analyseområdene
sine, men ikke angir kolonnen Rute, forutsetter FRAM at du vil ha like konsekvenser på alle ruter i hvert analyseområde.)


Følsomhetsanalyser
~~~~~~~~~~~~~~~~~~

FRAM tillater kjøring av følsomhetsanalyser med vilkårlige faktorer. Per versjon 3.4 er det bare mulig å endre på de følgende verdiene, som alle utgjør input til virkninger:
 - Trafikkvolum
 - Ulykkesfrekvens
 - Investeringskostnader
 - Vedlikeholdskostnader
 - Tidskostnader
 - Karbonpriser i tråd med Finansdepartementets rundskriv r-109/21.

Etter at modellen er kjørt med følsomhetsanalyser så kan resultatene hentes fra modellobjektet enten gjennom ``verdsatt_netto``, der hver følsomhetsanalyse korresponderer med et analysenavn, eller ved å oppgi analysenavnet som argument i ``kontantstrommer()``. I tillegg vil kontantstrømmene med netto nåverdi skrives til egne ark i output for hver følsomhetsanalyse.


Spesifisering av faktorer
=========================
For å gjennomføre følsomhetsanalyser i FRAM må man spesifisere ``folsomhetsanalyser``-argumentet når man initialiserer modellen. Argumentet kan enten være en dictionary, en iterable med tall eller ``True``.

Den enkleste måten å kjøre følsomhetsanalysene er ved å oppgi ``folsomhetsanalyser=True`` som vist under. Da vil modellen kjøre fire følsomhetsanalyser med faktorene 0.8 og 1.2 og de to følsomhetsanalysene for karbon som R-109 krever, med navn hhv. "følsomhetsanalyse_0.8" og "følsomhetsanalyse_1.2" , "høy karbonprisbane" og "lav karbonprisbane".

.. code-block:: python

    fram_modell = FRAM(
        FRAM_DIRECTORY / "eksempler" / "strekning 11.xlsx",
        tiltakspakke=11,
        ra_dir=FRAM_DIRECTORY / "eksempler" / "risikoanalyser",
        folsomhetsanalyser=True
    )

    fram_modell.run()
    fram_modell.kontantstrommer("følsomhetsanalyse_0.8")
    >> returnerer kontantstrømmene for følsomhetsanalysen med faktor 0.8.

Dersom man ønsker andre faktorer, eller vil kjøre flere følsomhetsanalyser, så kan man oppgi en iterable (f.eks. en liste) med faktorer. Modellen vil da kjøre én følsomhetsanalyse per faktor i listen, og navngi dem "følsomhetsanalyse_<faktor_1>", "følsomhetsanalyse_<faktor_2>" osv. i rekkefølgen faktorene ble oppgitt.

.. code-block:: python

    fram_modell = FRAM(
        FRAM_DIRECTORY / "eksempler" / "strekning 11.xlsx",
        tiltakspakke=11,
        ra_dir=FRAM_DIRECTORY / "eksempler" / "risikoanalyser",
        folsomhetsanalyser=[0.5, 0.75, 1.25, 1.5]
    )

    fram_modell.run()
    fram_modell.kontantstrommer("følsomhetsanalyse_0.5")
    >> returnerer kontantstrømmene for følsomhetsanalysen med faktor 0.5.

Man kan også kjøre følsomhetsanalyser med forskjellige faktorer for de forskjellige verdiene som påvirkes av følsomhetsanalyser. Dette gjøres ved å oppgi en nøstet dictionary med analysenavn som nøkler og nye dicts med verdinavn som nøkler og faktorer som verdier som verdier. Verdier som ikke oppgis blir satt til 1. Verdiene som kan oppgis er:

    -   "Investeringskostnader"
    -   "Vedlikehold"
    -   "Trafikkvolum"
    -   "Ulykkesfrekvens"
    -   "Tidskostnader"

.. code-block:: python

    fram_modell = FRAM(
        FRAM_DIRECTORY / "eksempler" / "strekning 11.xlsx",
        tiltakspakke=11,
        ra_dir=FRAM_DIRECTORY / "eksempler" / "risikoanalyser",
        folsomhetsanalyser = {
            "Analyse 1": {
                          "Investeringskostnader": 1.2,
                          "Vedlikehold" : 1.2,
                          "Ulykkesfrekvens": 1.4,
                          "Trafikkvolum" : 1.5
                          },
            "Analyse 2": {
                          "Tidskostnader": 0.7,
                          "Drivstoff": 0.8,
                          "Trafikkvolum" : 1.5
                          }
        },
    )

    fram_modell.run()
    fram_modell.kontantstrommer("Analyse 1")
    >> returnerer kontantstrømmene for følsomhetsanalysen med faktorene
    >> spesifisert i dicten med nøkkelverdi "Analyse 1"

Dette tillater egentlig svært komplekse og omfattende følsomhetsanalyser, og tidsbruken til FRAM skalerer veldig godt med antall følsomhetsanalyser. Til inspirasjon kunne man ha generert dictionarien `folsomhetsanalyser` maskinelt, slik som under her:

.. code-block:: python

    import random
    parametere = [random.normalvariate(mu=1, sigma=0.2) for _ in range(10)] # Eller hentet fra en helt annen kilde, for eksempel en empirisk fordeling basert på historiske skift i trafikken
    folsomhetsanalyser = {f"analyse_{par}": {"Trafikkvolum": par} for par in parametere}
    # Dette vl gi deg en dict som ser slik ut:
    # {'analyse_1.083171293254913': {'Trafikkvolum': 1.083171293254913},
    #  'analyse_1.0000834825636733': {'Trafikkvolum': 1.0000834825636733},
    #  'analyse_1.077463445036401': {'Trafikkvolum': 1.077463445036401},
    #  'analyse_1.2712765404112236': {'Trafikkvolum': 1.2712765404112236},
    #  'analyse_1.0959111926223486': {'Trafikkvolum': 1.0959111926223486},
    #  'analyse_0.8607565209088969': {'Trafikkvolum': 0.8607565209088969},
    #  'analyse_0.9051818905096853': {'Trafikkvolum': 0.9051818905096853},
    #  'analyse_0.7045436828916716': {'Trafikkvolum': 0.7045436828916716},
    #  'analyse_0.9664271429268626': {'Trafikkvolum': 0.9664271429268626},
    #  'analyse_1.0623381718731664': {'Trafikkvolum': 1.0623381718731664}}


Output og informasjon som ligger på FRAM
------------------------------------------
Etter å ha kjørt run() skriver modellen automatisk output til en mappe som heter ``Output <TILTAKSPAKKENR>``, der ``<TILTAKSPAKKENR>`` er tiltakspakkenummeret som indikert i inputfilen og i initialiseringen av modellen. I denne mappen vil det ligge tre filer: ``Resultater <TILTAKSPAKKENR>.xlsx`` inneholder en oppsummering av resultatene fra hovedkjøringen og eventuelle følsomhetsanalyser, ``Detaljerte resultater<TILTAKSPAKKENR>.xlsx`` inneholder detaljerte resultater om verdsatte virkninger og volumvirkninger, og ``Dashbord <TILTAKSPAKKENR>.html`` inneholder dashbord som gir oversikt over resultatene.

.. code-block:: python

    fram_modell.run(
        skriv_output=False
    )
    >> Skriver ingen output etter kjøring

    fram_modell.run(
        skriv_output="/Users/bruker/Dokumenter/fram_resultater/"
    )
    >> Skriver output til den angitte mappen.

Man kan også benytte seg av fram-objektet som nå er generert, og hente ut data for videre manipulasjon. For eksempel ligger alle virkningene som er beregnet
under `fram_modell.virkninger`, og man kan se på volumvirkningene i tiltaksbanen for en konkret virkning ved å skrive `fram_modell.virkninger.drivstoff.volumvirkning_tiltak`.




Valideringer
------------
Valideringer:

	- Man må alltid angi strekning og tiltakspakke. Strekningen må vise til en gyldig inputfil på .xlsx-format. Inputfilen har en lang rette formkrav som er dokumentert i filen.
	- Man må bruke predefinerte skipstyper og lengdegrupper i tråd med Kystverkets kategorisering
	- Man må spesifisere at man skal kjøre en delvis FRAM dersom man ikke har med all input som kreves for å kjøre en fullstendig FRAM.
	- Dersom man har trafikkoverføringer. Modellen gjør en sjekk av at alle skipsoverføringer (inkludert de man også antar at blir værende på samme rute) summerer seg til 100 prosent slik at ingen skip blir borte som følge av trafikkoverføringen.
	- Man må ha prognoser for alle kombinasjoner av skipstyper og lengdegrupper som inngår i trafikkgrunnlaget.
	- Hva man må ha av input for ulike virkninger
		○ Tidsavhengige kostnader: Trafikk, endring i tid og kalkulasjonspriser for alle skip som får tidsendring.
		○ Distanseavhengige kostnader: Trafikk, endring i tid/hastighet, tankested (må være "nord", "sør" eller "int")
		○ Risikovirkninger: Trafikk, risikoanalyse for referanse- og tiltaksbane på strengt format, tidsavhengige kalkulasjonspriser. Krever konsistent bruk av risikonavn mellom selve risikoanalysene og spesifisering i inputarket.
		○ Ventetidskostnader: Du må ha de samme skipene i både tiltak og referansebane, og du må ha trafikkgrunnlag for alle som har ventetid, kalkulasjonspriser for tid
		○ Tid ute av drift:  Trafikk, endring i tid/hastighet
		○ Investeringskostnader: kostnader og kroneår som ligger til grunn for kostnadsberegningen
		○ Sedimenter: Areal, tilstandsendring og kommune
		○ Vedlikeholdskostnader: Endring i antall merker gitt predefinerte merketyper


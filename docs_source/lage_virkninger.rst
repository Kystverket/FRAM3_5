================================================================================
Hvordan bruke virkningene i FRAM, og hvordan kjøre enkeltvirkninger separat?
================================================================================

FRAM er per versjon 3.5 satt opp slik at hver virkning beregnes av en egen modul, mens FRAM-klassen som importeres har som oppgave å klargjøre input og output etter Kystverkets spesifikasjoner. Dette innebærer at hver virkning også kan kjøres uavhengig av FRAM.

Dersom man har input på samme format som forventes av FRAM, og ønsker å benytte de samme forutsetningene som i FRAM, så går det an å kjøre virkningen gjennom et :py:class:`~fram.modell.FRAM`-objekt, som ved vanlig SØA. Den eneste forskjellen skal da være at ``delvis_fram=True`` må oppgis som argument i instansieringen. Forsidearket trengs for alle kjøringer gjennom FRAM.


++++++++++++++++++++++
Kjøre virkninger alene
++++++++++++++++++++++

Hver virkning kan også kjøres alene. De tilgjengelige virkningene er:

.. code-block:: python

    from fram.virkninger import (
        Tidsbruk,
        Drivstoff,
        Utslipp_til_luft,
        Risiko,
        Vedlikeholdskostnader,
        Investeringskostnader,
        Kontantstrommer,
        Sedimenter,
        Ventetid
    )

Alle virkningene arver fra den samme grunnklassen `fram.virkninger.virkning.Virkning`,
og har det samme, grunnleggende grensesnittet:

- Funksjonen ``beregn()`` for å beregne virkningen
- DataFramene ``verdsatt_brutto_ref``, ``verdsatt_brutto_tiltak`` og ``verdsatt_netto`` som inneholder de verdsatte virkningene per år. Samme format som i FRAM, :py:mod:`se schema her <fram.generelle_hjelpemoduler.schemas.VerdsattSchema>`.
- DataFramene ``volumvirkning_ref`` og ``volumvirkning_tiltak`` som inneholder de volumvirkningene per år, der det er relevant. Samme format som volumvirkningene i FRAM, :py:mod:`se schema her <fram.generelle_hjelpemoduler.schemas.VolumSchema>`.
- Funksjonen ``get_naaverdi()`` for å hente neddiskontert nåverdi med renter som angitt i rentebanen, for hvert år i rentebanen.

Du kan lese mer om det felles grunnlaget for virkningene her: :py:meth:`~fram.virkninger.virkning.Virkning`.
Mange av virkningene har FRAMs standard aggregeringskolonner som indeks. Disse kolonnene er ``Strekning``, ``Tiltaksomraade``, ``Tiltakspakke``, ``Analyseomraade``, ``Rute``, ``Skipstype`` og ``Lengdegruppe``.

Tidsbruk
++++++++

:doc:`Tidsbruk er modulen for verdsetting av tidsavhengige kostnader. <fram.virkninger.tid.virkning>`

Klassen instansieres slik:

.. code-block:: python

    tid = Tidsbruk(
        beregningsaar,
        kalkulasjonspriser
    )

- **beregningsaar**: En liste med årene virkningen skal beregnes for
- **kalkulasjonspriser**: Kalkulasjonspriser for tidsbruk per skipstype per lengdegruppe. En pandas DataFrame som inneholder årstallskolonner samt skipstype og lengdegruppe. :py:mod:`Se schema her. <fram.virkninger.tid.schemas.KalkprisTidSchema>`

Objektet kan så beregne virkninger slik:

.. code-block:: python

    tid.beregn(
        tidsbruk_per_passering_ref,
        tidsbruk_per_passering_tiltak,
        trafikk_ref,
        trafikk_tiltak,
    )

- **tidsbruk_per_passering_ref**: Tidsbruk per passering i referansebanen. DataFrame med standard aggregeringskolonner som indeks, og årskolonner med ikke-negative verdier. :py:mod:`Se schema her. <fram.generelle_hjelpemoduler.schemas.TidsbrukPerPassSchema>`
- **tidsbruk_per_passering_tiltak**: Tidsbruk per passering i tiltaksbanen. DataFrame med standard aggregeringskolonner som indeks, og årskolonner med ikke-negative verdier. :py:mod:`Se schema her. <fram.generelle_hjelpemoduler.schemas.TidsbrukPerPassSchema>`
- **trafikk_ref**: Årlige passeringer per skipstype per lengdegruppe i referansebanen. DataFrame med standard aggregeringskolonner samt ``Analysenavn`` som indeks, og årskolonner med ikke-negative verdier. :py:mod:`Se schema her. <fram.generelle_hjelpemoduler.schemas.TrafikkGrunnlagSchema>`
- **trafikk_tiltak**: Årlige passeringer per skipstype per lengdegruppe i tiltaksbanen. DataFrame med standard aggregeringskolonner samt ``Analysenavn`` som indeks, og årskolonner med ikke-negative verdier. :py:mod:`Se schema her. <fram.generelle_hjelpemoduler.schemas.TrafikkGrunnlagSchema>`


Drivstoff
+++++++++

:doc:`Drivstoff er modulen som beregner distanseavhengige kostnader <fram.virkninger.drivstoff.virkning>`

Klassen instansieres slik:

.. code-block:: python

    drivstoff = Drivstoff(
        beregningsaar,
        tankested,
        kroneaar
    )

- **beregningsaar**: En liste med årene virkningen skal beregnes for
- **tankested**: "nord" eller "sør" (for trondheim).
- **kroneaar**: Kroneåret for kalkprisene virkningen beregner selv

Objektet kan så beregne virkninger slik:

.. code-block:: python

    drivstoff.beregn(
        tidsbruk_per_passering_ref,
        tidsbruk_per_passering_tiltak,
        hastighet_per_passering_ref,
        hastighet_per_passering_tiltak,
        trafikk_ref,
        trafikk_tiltak,
    )

- **tidsbruk_per_passering_ref**: Tidsbruk per passering i referansebanen. DataFrame med standard aggregeringskolonner som indeks, og årskolonner med ikke-negative verdier. :py:mod:`Se schema her. <fram.generelle_hjelpemoduler.schemas.TidsbrukPerPassSchema>`
- **tidsbruk_per_passering_tiltak**: Tidsbruk per passering i tiltaksbanen. DataFrame med standard aggregeringskolonner som indeks, og årskolonner med ikke-negative verdier. :py:mod:`Se schema her. <fram.generelle_hjelpemoduler.schemas.TidsbrukPerPassSchema>`
- **hastighet_per_passering_ref**: Hastighet per passering i referansebanen. DataFrame med ``Rute, Skipstype, Lengdegruppe`` som indeks, og en kolonne ``Hastighet`` med ikke-negative verdier. :py:mod:`Se schema her. <fram.virkninger.drivstoff.schemas.HastighetSchema>`
- **hastighet_per_passering_tiltak**: Hastighet per passering i tiltaksbanen. DataFrame med ``Rute, Skipstype, Lengdegruppe`` som indeks, og en kolonne ``Hastighet`` med ikke-negative verdier. :py:mod:`Se schema her. <fram.virkninger.drivstoff.schemas.HastighetSchema>`
- **trafikk_ref**: Årlige passeringer per skipstype per lengdegruppe i referansebanen. DataFrame med` standard aggregeringskolonner samt ``Analysenavn`` som indeks, og årskolonner med ikke-negative verdier. :py:mod:`Se schema her. <fram.generelle_hjelpemoduler.schemas.TrafikkGrunnlagSchema>`
- **trafikk_tiltak**: Årlige passeringer per skipstype per lengdegruppe i tiltaksbanen. DataFrame med standard aggregeringskolonner samt ``Analysenavn`` som indeks, og årskolonner med ikke-negative verdier. :py:mod:`Se schema her. <fram.generelle_hjelpemoduler.schemas.TrafikkGrunnlagSchema>`


Risiko
++++++

:doc:`Risiko er modulen som beregner kostnader forbundet med ulykker <fram.virkninger.risiko.virkning>`

Klassen instansieres slik:

.. code-block:: python

    risiko = Risiko(
        beregningsaar,
        sarbarhet,
        kalkpriser_materielle_skader,
        kalkpriser_helse,
        kalkpriser_oljeutslipp,
        kalkpriser_oljeopprensking,
        kalkpriser_tid,
        kroneaar
    )

- **beregningsaar**: En liste med årene virkningen skal beregnes for
- **sarbarhet**: DataFrame med sårbarhetsvurdering for de berørte områdene. Må ha kolonnene ``Strekning, Tiltaksomraade, Tiltakspakke, Analyseomraade, Fylke``, samt ``Saarbarhet``, som kan ta verdiene "lav", "moderat", "hoy" eller "svaart hoy". :py:mod:`Se schema her. <fram.virkninger.risiko.schemas.SarbarhetSchema>`
- **kalkpriser_materielle_skader**: Kalkulasjonspriser for materielle skader. Skal ha ``Skipstype, Lengdegruppe, Hendelsestype``som indeks, der ``Hendelsestype``er en av "Grunnstøting", "Kontaktskade", "Striking", "Struck". Årskolonner med positive tall. :py:mod:`Se schema her. <fram.virkninger.risiko.schemas.KalkprisMaterielleSchema>`
- **kalkpriser_helse**: Kalkulasjonspriser for personskader og dødsfall. Skal ha ``Konsekvens``som indeks, med verdiene "Dodsfall" og "Personskade". Årskolonner med positive tall. :py:mod:`Se schema her. <fram.virkninger.risiko.schemas.KalkprisHelseSchema>`
- **kalkpriser_oljeutslipp**: Kalkulasjonspriser for skader som følge av oljeutslipp. Må inneholde kolonnene ``Skipstype, Lengdegruppe, Hendelsestype, Sarbarhet, Fylke``, der ``Hendelsestype`` må ha en av verdiene "Grunnstøting", "Kontaktskade", "Striking" og "Struck" og ``Sarbarhet`` har en av verdiene "lav", "moderat", "hoy" og "svaart hoy".
- **kalkpriser_oljeopprensking**: Kalkulasjonspriser for opprensing av oljeutslipp. Må inneholde kolonnene ``Skipstype, Lengdegruppe, Hendelsestype``, der ``Hendelsestype`` må ha en av verdiene "Grunnstøting", "Kontaktskade", "Striking" og "Struck".
- **kalkpriser_tid**: Kalkulasjonspriser for tidsbruk per skipstype per lengdegruppe. En pandas DataFrame som inneholder årstallskolonner samt skipstype og lengdegruppe. :py:mod:`Se schema her. <fram.virkninger.tid.schemas.KalkprisTidSchema>`
- **kroneaar**: Kroneåret for kalkprisene virkningen beregner selv

Objektet kan så beregne virkninger slik:

.. code-block:: python

    risiko.beregn(
        hendelser_ref,
        hendelser_tiltak
    )

- **tidsbruk_per_passering_ref**: Tidsbruk per passering i referansebanen. DataFrame med standard aggregeringskolonner som indeks, og årskolonner med ikke-negative verdier. :py:mod:`Se schema her. <fram.generelle_hjelpemoduler.schemas.TidsbrukPerPassSchema>`
- **tidsbruk_per_passering_tiltak**: Tidsbruk per passering i tiltaksbanen. DataFrame med standard aggregeringskolonner som indeks, og årskolonner med ikke-negative verdier. :py:mod:`Se schema her. <fram.generelle_hjelpemoduler.schemas.TidsbrukPerPassSchema>`
- **hastighet_per_passering_ref**: Hastighet per passering i referansebanen. DataFrame med indeks ``Rute, Skipstype, Lengdegruppe``, og en kolonne ``Hastighet`` med ikke-negative verdier. :py:mod:`Se schema her. <fram.virkninger.drivstoff.schemas.HastighetSchema>`
- **hastighet_per_passering_tiltak**: Hastighet per passering i tiltaksbanen. DataFrame med indeks ``Rute, Skipstype, Lengdegruppe``, og en kolonne ``Hastighet`` med ikke-negative verdier. :py:mod:`Se schema her. <fram.virkninger.drivstoff.schemas.HastighetSchema>`
- **trafikk_ref**: Årlige passeringer per skipstype per lengdegruppe i referansebanen. DataFrame med standard aggregeringskolonner samt ``Analysenavn`` som indeks, og årskolonner med ikke-negative verdier. :py:mod:`Se schema her. <fram.generelle_hjelpemoduler.schemas.TrafikkGrunnlagSchema>`
- **trafikk_tiltak**: Årlige passeringer per skipstype per lengdegruppe i tiltaksbanen. DataFrame med standard aggregeringskolonner samt ``Analysenavn`` som indeks, og årskolonner med ikke-negative verdier. :py:mod:`Se schema her. <fram.generelle_hjelpemoduler.schemas.TrafikkGrunnlagSchema>`

Investeringskostnader
+++++++++++++++++++++

:doc:`Investeringskostnader er modulen som beregner investeringskostnader. <fram.virkninger.investering.virkning>`

Klassen instansieres slik:

.. code-block:: python

    investering = Investeringskostnader(
        beregningsaar,
        kroneaar,
        strekning
    )

- **beregningsaar**: En liste med årene virkningen skal beregnes for
- **kroneaar**: Kroneåret for kalkprisene virkningen beregner selv
- **strekning**: Navnet på strekningen som investeringene gjennomføres for.

Objektet kan så beregne virkninger slik:

.. code-block:: python

    investering.beregn(
        investeringskostnader_tiltak,
        investeringskostnader_ref,
    )

- **investeringskostnader_tiltak**: Investeringskostnader i tiltaksbanen. DataFrame med kolonnene ``Tiltaksomraade, Tiltakspakke, Investeringstype, P50 (kroner), Forventningsverdi (kroner), Første år med kostnader, Siste år med kostnader`` der ``Investeringstype`` er en av verdiene "Utdyping", "Navigasjonsinnretninger" og "Annet". :py:mod:`Se schema her. <fram.generelle_hjelpemoduler.schemas.TidsbrukPerPassSchema>`
- **investeringskostnader_ref**: Investeringskostnader i referansebanen. DataFrame med kolonnene ``Tiltaksomraade, Tiltakspakke, Investeringstype, P50 (kroner), Forventningsverdi (kroner), Første år med kostnader, Siste år med kostnader`` der ``Investeringstype`` er en av verdiene "Utdyping", "Navigasjonsinnretninger" og "Annet". Trenger ikke oppgis. :py:mod:`Se schema her. <fram.generelle_hjelpemoduler.schemas.TidsbrukPerPassSchema>`


Vedlikeholdskostnader
+++++++++++++++++++++

:doc:`Vedlikeholdskostnader er modulen som beregner kostnader for løpende vedlikehold og nødvendige oppgraderinger <fram.virkninger.vedlikehold.virkning>`

Vedlikehold kan beregnes for følgende objekttyper:

- Lyktehus på stativ
- Lyktehus på søyle
- Lyktehus på underbygning
- Lyktehus på varde
- HIB på stativ
- HIB på søyle
- HIB på stang
- HIB på varde
- IB på stativ
- IB på søyle
- IB på stang
- IB på varde
- Lanterne på stativ
- Lanterne på søyle
- Lanterne på stang
- Lanterne på varde
- Lysbøye i glassfiber
- Lysbøye i stål
- Båke
- Stake
- Stang
- Varde
- Fyrstasjon

Klassen instansieres slik:

.. code-block:: python

    vedlikehold = Vedlikehold(
        strekning,
        tiltakspakke,
        kostnader,
        oppgrad,
        beregningsaar,
        ferdigstillelsesaar,
        sluttaar
    )

- **strekning**: Navnet på strekningen som vedlikeholdskostnadene skal beregnes for.
- **tiltakspakke**: Navnet på tiltakspakken som vedlikeholdskostnadene skal beregnes for.
- **kostnader**: Løpende kostnader for objekttyper. Må ha ``Objekttype, Analysenavn`` som indeks, der ``Objekttype`` tar verdier som inngår i listen over. :py:mod:`Se schema her. <fram.virkninger.vedlikehold.schemas.VedlikeholdskostnaderSchema>`
- **oppgrad**: Kostnader for nødvendige oppgraderinger. Må ha ``Objekttype, Analysenavn`` som indeks, der ``Objekttype`` tar verdier som inngår i listen over. Må ha kolonnene ``Total, TG0->TG2, TG1->TG2, Kroneverdi`` der ``Total`` er kostnaden for oppgraderingen, ``TG0->TG2`` er tiden et nytt objekt bruker før det trenger oppgradering, og ``TG0->TG1`` er tiden et tidligere oppgradert objekt bruker før det trenger oppgradering. :py:mod:`Se schema her. <fram.virkninger.vedlikehold.schemas.VedlikeholdskostnaderSchema>`
- **beregningsaar**: En liste med årene virkningen skal beregnes for
- **ferdigstillelsesaar**: Året tiltaket er ferdigstilt
- **sluttaar**: Siste år kostnader skal beregnes for

Objektet kan så beregne virkninger slik:

.. code-block:: python

    vedlikehold.beregn(
        vedlikeholdsobjekter
    )

- **vedlikeholdsobjekter**: DataFrame med vedlikeholdsobjekter som skal settes opp eller fjernes i tiltaket. DataFrame med kolonnene ``Objekttype, Endring``, der ``Objekttype`` tar verdier som inngår i listen over. :py:mod:`Se schema her. <fram.virkninger.vedlikehold.schemas.VedlikeholdsobjekterSchema>`


Sedimenter
++++++++++

:doc:`Sedimenter er modulen som beregner kostnader fra forurensede sedimenter <fram.virkninger.sedimenter.virkning>`

Klassen instansieres slik:

.. code-block:: python

    sedimenter = Sedimenter(
        ferdigstillelsesaar,
        beregningsaar,
        kroneaar,
    )

- **ferdigstillelsesaar**: Året tiltaket er ferdigstilt
- **beregningsaar**: En liste med årene virkningen skal beregnes for
- **kroneaar**: Kroneåret for kalkprisene virkningen beregner selv

Objektet kan så beregne virkninger slik:

.. code-block:: python

    sedimenter.beregn(
        forurenset_tiltak
        forurenset_ref
    )

- **forurenset_tiltak**: DataFrame med tilstanden til sedimentene i utdypingsområdet etter tiltak. Må ha kolonnene ``Tiltaksomraade, Analyseomraade, Utdypingsområde, tilstandsendring, kommunenavn``. ``tilstandsendring`` må ha verdier på formatet ``<FARGE> -> <FARGE>`` der ``<FARGE>`` er enten "Rød", "Oransje", "Gul" eller "Grønn". :py:mod:`Se schema her. <fram.virkninger.sedimenter.schemas.ForurensingSchema>`
- **forurenset_ref**:  DataFrame med tilstanden til sedimentene i utdypingsområdet før tiltak. Må ha kolonnene ``Tiltaksomraade, Analyseomraade, Utdypingsområde, tilstandsendring, kommunenavn``. ``tilstandsendring`` må ha verdier på formatet ``<FARGE> -> <FARGE>`` der ``<FARGE>`` er enten "Rød", "Oransje", "Gul" eller "Grønn". Kan være None. :py:mod:`Se schema her. <fram.virkninger.sedimenter.schemas.ForurensingSchema>`

Utslipp_til_luft
++++++++++++++++

:doc:`Utslipp_til_luft er modulen som beregner kostnader forbundet med lokale og globale utslipp til atmosfæren <fram.virkninger.utslipp_til_luft.virkning>`

Klassen instansieres slik:

.. code-block:: python

    utslipp_til_luft = Utslipp_til_luft(
        beregningsaar,
        kroneaar
    )

- **beregningsaar**: En liste med årene virkningen skal beregnes for
- **kroneaar**: Kroneåret for kalkprisene virkningen beregner selv

Objektet kan så beregne virkninger slik:

.. code-block:: python

    utslipp_til_luft.beregn(
        tidsbruk_per_passering_ref,
        tidsbruk_per_passering_tiltak,
        hastighet_per_passering_ref,
        hastighet_per_passering_tiltak,
        trafikk_ref,
        trafikk_tiltak,
        kalkpris_utslipp_til_luft
    )

- **tidsbruk_per_passering_ref**: Tidsbruk per passering i referansebanen. DataFrame med standard aggregeringskolonner som indeks, og årskolonner med ikke-negative verdier. :py:mod:`Se schema her. <fram.generelle_hjelpemoduler.schemas.TidsbrukPerPassSchema>`
- **tidsbruk_per_passering_tiltak**: Tidsbruk per passering i tiltaksbanen. DataFrame med standard aggregeringskolonner som indeks, og årskolonner med ikke-negative verdier. :py:mod:`Se schema her. <fram.generelle_hjelpemoduler.schemas.TidsbrukPerPassSchema>`
- **hastighet_per_passering_ref**: Hastighet per passering i referansebanen. DataFrame med ``Rute, Skipstype, Lengdegruppe`` som indeks, og en kolonne ``Hastighet`` med ikke-negative verdier. :py:mod:`Se schema her. <fram.virkninger.drivstoff.schemas.HastighetSchema>`
- **hastighet_per_passering_tiltak**: Hastighet per passering i tiltaksbanen. DataFrame med ``Rute, Skipstype, Lengdegruppe`` som indeks, og en kolonne ``Hastighet`` med ikke-negative verdier. :py:mod:`Se schema her. <fram.virkninger.drivstoff.schemas.HastighetSchema>`
- **trafikk_ref**: Årlige passeringer per skipstype per lengdegruppe i referansebanen. DataFrame med` standard aggregeringskolonner samt ``Analysenavn`` som indeks, og årskolonner med ikke-negative verdier. :py:mod:`Se schema her. <fram.generelle_hjelpemoduler.schemas.TrafikkGrunnlagSchema>`
- **trafikk_tiltak**: Årlige passeringer per skipstype per lengdegruppe i tiltaksbanen. DataFrame med standard aggregeringskolonner samt ``Analysenavn`` som indeks, og årskolonner med ikke-negative verdier. :py:mod:`Se schema her. <fram.generelle_hjelpemoduler.schemas.TrafikkGrunnlagSchema>`
- **kalkpris_utslipp_til_luft**: DataFrame med kalkulasjonspriser for utslipp til luft. Må ha kolonnene ``Utslipp, Kroneverdi, Område`` der ``Utslipp`` har verdiene "CO2", "NOX", "PM10", samt årskolonner med kalkulasjonsprisene.

Ventetid
++++++++

:doc:`Ventetid er modulen som beregner kostnader fra ventetid for skip <fram.virkninger.ventetid.virkning>`

Klassen instansieres slik:

.. code-block:: python

    ventetid = Ventetid(
        kalkpris_tid,
        trafikk_ref,
        trafikk_tiltak,
        beregningsaar
    )

- **kalkpris_tid**: Kalkulasjonspriser for tidsbruk per skipstype per lengdegruppe. En pandas DataFrame som inneholder årstallskolonner samt skipstype og lengdegruppe. :py:mod:`Se schema her. <fram.virkninger.tid.schemas.KalkprisTidSchema>`
- **trafikk_ref**: Årlige passeringer per skipstype per lengdegruppe i referansebanen. DataFrame med` standard aggregeringskolonner samt ``Analysenavn`` som indeks, og årskolonner med ikke-negative verdier. :py:mod:`Se schema her. <fram.generelle_hjelpemoduler.schemas.TrafikkGrunnlagSchema>`
- **trafikk_tiltak**: Årlige passeringer per skipstype per lengdegruppe i tiltaksbanen. DataFrame med standard aggregeringskolonner samt ``Analysenavn`` som indeks, og årskolonner med ikke-negative verdier. :py:mod:`Se schema her. <fram.generelle_hjelpemoduler.schemas.TrafikkGrunnlagSchema>`
- **beregningsaar**: En liste med årene virkningen skal beregnes for

Objektet kan så beregne virkninger slik:

.. code-block:: python

    utslipp_til_luft.beregn(
        simuleringsinput_ref,
        metadatakolonner,
        simuleringsinput_tiltak,
        seed
    )

- **simuleringsinput_ref**: :py:mod:`Simuleringsinput for referansebanen. <fram.virkninger.ventetid.hjelpemoduler.SimuleringsInput>`
- **metadatakolonner**: DataFrame med kolonner som definerer metakolonnene for simuleringsinputen.
- **simuleringsinput_tiltak**: :py:mod:`Simuleringsinput for tiltaksbanen. <fram.virkninger.ventetid.hjelpemoduler.SimuleringsInput>`

Kontantstrømmer
+++++++++++++++
:doc:`Kontantstrømmer er modulen som beregner kostnader og gevinster for andre, brukerdefinerte kontantstrømmer <fram.virkninger.kontantstrommer.virkning>`

Klassen instansieres slik:

.. code-block:: python

    kontantstrommer = Kontantstrommer(
        beregningsaar,
        kroneaar,
        strekning
    )

- **beregningsaar**: En liste med årene virkningen skal beregnes for
- **kroneaar**: Kroneåret for kalkprisene virkningen beregner selv
- **strekning**: Navnet på strekningen som kontantstrømmene gjelder for.

Objektet kan så beregne virkninger slik:

.. code-block:: python

    kontantstrommer.beregn(
        ytterlige_kontantstrommer_tiltak,
        ytterlige_kontantstrommer_ref
    )

- **ytterlige_kontantstrommer_tiltak**: DataFrame med kontantstrømmer i tiltaksbanen. Må ha kolonnen ``Kroneverdi``, og kan ha kolonnen ``Andel skattefinansieringskostnad`` og ``Aktør``. Årskolonner med kontantstrømmene. :py:mod:`Se schema her. <fram.virkninger.kontantstrommer.schemas.KontantstromSchema>`
- **ytterlige_kontantstrommer_ref**: DataFrame med kontantstrømmer i referansebanen. Må ha kolonnen ``Kroneverdi``, og kan ha kolonnen ``Andel skattefinansieringskostnad`` og ``Aktør``. Årskolonner med kontantstrømmene. :py:mod:`Se schema her. <fram.virkninger.kontantstrommer.schemas.KontantstromSchema>`
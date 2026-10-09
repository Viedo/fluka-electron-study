# Test instalacji FLUKA

Ten mały przypadek służy do sprawdzenia przyszłej instalacji, uruchamiania i odczytu wyników. **Nie został uruchomiony w FLUKA ani zwalidowany fizycznie.** Parametry są roboczym przykładem, który później zastąpimy właściwym modelem.

| Element | Ustawienie |
| --- | --- |
| Źródło | Fotony 1 MeV, punkt `(0, 0, -1)` cm w próżni, kierunek `+z`, bez rozrzutu energii i kierunku |
| Obiekt | Woda: `x, y = -5…5 cm`, `z = 0…10 cm` |
| Otoczenie | Próżnia w kuli o promieniu 100 cm; dalej powłoka `BLCKHOLE` do promienia 100000 cm |
| Fizyka | `DEFAULTS PRECISIO`, bez dodatkowych zmian progów |
| Statystyka | Maksymalnie 1000 historii na cykl, początkowy identyfikator sekwencji `1234567` |
| Zapis | `USRBIN ENERGY`, siatka kartezjańska `21 × 21 × 20` pokrywająca wodę, wyjście binarne na jednostce 21 |

Ujemne `BEAM WHAT(1) = -0.001` oznacza energię kinetyczną w GeV. `WATER` jest materiałem predefiniowanym o gęstości 1 g/cm³; nie potrzeba osobnej definicji składu. Źródła: [BEAM](https://flukafiles.web.cern.ch/manual/chapters/description_input/description_options/beam.html), [BEAMPOS](https://flukafiles.web.cern.ch/manual/chapters/description_input/description_options/beampos.html), [materiały](https://flukafiles.web.cern.ch/manual/chapters/particle_and_material_codes/pre-defined_materials.html), [DEFAULTS](https://flukafiles.web.cern.ch/manual/chapters/description_input/description_options/defaults.html).

`DEFAULTS` zachowuje format kolumnowy (SDUM zaczyna się w kolumnie 71), aby poprzedzać pozostałe ustawienia. Dalej karta `FREE` umożliwia zapis parametrów oddzielanych spacjami; podajemy wszystkie sześć pól WHAT. Geometrię nazwową włącza `GEOBEGIN … COMBNAME`; jej linia tytułu nadal zachowuje układ kolumnowy. Źródła: [FREE](https://flukafiles.web.cern.ch/manual/chapters/description_input/description_options/free.html), [GEOBEGIN](https://flukafiles.web.cern.ch/manual/chapters/description_input/description_options/geobegin.html), [tytuł geometrii](https://flukafiles.web.cern.ch/manual/chapters/combinatorial_geometry/combinatorial_geometry_input/geometry_title_line.html).

`USRBIN` typu 10 rozdziela depozycję energii wzdłuż kroku cząstki. Wynik `ENERGY` ma jednostkę **GeV/cm³ na jednostkę wagi cząstki pierwotnej**, czyli tutaj na jeden foton źródła. Jest już znormalizowany: nie dziel go ponownie przez 1000 ani przez objętość komórki. Aby uzyskać średnią energię zdeponowaną w wodzie na foton, sumuje się wartości pomnożone przez objętość komórki `(10/21) × (10/21) × 0.5 cm³`. Nie jest to bezpośrednio dawka w Gy. Nieparzyste liczby komórek w x/y umieszczają oś wiązki wewnątrz centralnej komórki. Źródło: [USRBIN](https://flukafiles.web.cern.ch/manual/chapters/description_input/description_options/usrbin.html).

Pierwsze uruchomienie planujemy na **jeden cykl**; liczbę cykli ustawia skrypt uruchamiający, a `START` ogranicza historie w pojedynczym cyklu. Taka statystyka wystarczy do kontroli działania, ale mapa może być bardzo zaszumiona, z wieloma zerami. Jeden cykl nie umożliwia oszacowania rozrzutu między cyklami. Do wyników naukowych trzeba zaplanować większą statystykę, niezależne sekwencje i analizę niepewności. Powtórzenie tego samego wejścia z tym samym stanem generatora nie daje niezależnej próby; `RANDOMIZ` może też wczytać zapisany stan generatora z poprzedniego cyklu. Źródła: [START](https://flukafiles.web.cern.ch/manual/chapters/description_input/description_options/start.html), [RANDOMIZ](https://flukafiles.web.cern.ch/manual/chapters/description_input/description_options/randomiz.html).

Po instalacji należy sprawdzić geometrię w Flair, odczytać echo parametrów i komunikaty FLUKA, potwierdzić zakończenie 1000 historii oraz poprawny odczyt danych jednostki 21. Samo powstanie pliku wynikowego nie potwierdza poprawności symulacji.

Dokumentację przygotowano według [manuala FLUKA.CERN 4-5.2](https://flukafiles.web.cern.ch/manual/index.html), dostępnego z [oficjalnej strony CERN](https://fluka.cern/documentation), sprawdzonego 2026-09-24.

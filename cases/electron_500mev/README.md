# Wiązka elektronów 0,5 GeV w ołowiu — przykład techniczny

Użytkownik wskazał wstępnie **elektrony o energii 0,5 GeV = 500 MeV**, a następnie przyjął roboczo **ołów** jako napromieniany materiał. Ten osobny przypadek przygotowuje wejście dla takiej wiązki i materiału. W pierwszym technicznym przebiegu wykonano 1000 historii na siatce 21×21×20; bieżące wejście zwiększa statystykę do 10 000 historii i rozdzielczość do 31×31×30. Żaden przebieg nie stanowi walidacji fizycznej. Wymiary obiektu i cel pomiaru pozostają do ustalenia w [założeniach symulacji](../../docs/zalozenia-symulacji.md).

Pierwszy przebieg: `runs/20261009T061821Z_electron_500mev_g0d6X60y/` (1000 historii). Drugi przebieg: `runs/20261009T063202Z_electron_500mev_iJ0KXKBU/` (10 000 historii; FLUKA 4-5.2, JEFF-3.3). Oba raporty zawierają ostrzeżenie BLCCRE o maksymalnym błędzie dopasowania 54.5%; trzeba je wyjaśnić przed dalszym użyciem wyniku.

Wykresy drugiego przebiegu znajdują się w `reports/generated/20261009T063202Z_electron_500mev_iJ0KXKBU/`: centralny przekrój x, trzy przekroje poprzeczne przy z ≈ 0.83, 4.83 i 8.83 cm, podłużny i promieniowy profil z CSV oraz widok 3D. Widok 3D pokazuje tylko woksele o depozycji ≥0,1% maksimum, by zachować czytelność. Wykresy są kopiowane również do `~/Desktop/FLUKA-wyniki/<run_id>/`. To jeden cykl, bez oszacowania niepewności; zwiększenie liczby historii i rozdzielczości nie zastępuje walidacji ani ustalenia parametrów eksperymentu.

Roboczo interpretujemy 0,5 GeV jako **energię kinetyczną** elektronu. Jeśli chodzi o energię całkowitą lub pęd, trzeba odpowiednio zmienić kartę `BEAM`. Ujemne `WHAT(1)` wybiera energię kinetyczną w GeV; `ELECTRON` określa elektrony:

```text
BEAM -0.5 0.0 0.0 0.0 0.0 1.0 ELECTRON
```

Znaczenie pól potwierdzono w [manualu CERN — BEAM](https://flukafiles.web.cern.ch/manual/chapters/description_input/description_options/beam.html). Dodatnia wartość pierwszego pola oznaczałaby pęd w GeV/c.

## Założenia przykładu

Materiał `LEAD` wynika z roboczego wyboru użytkownika. Pozostałe parametry poniżej służą wyłącznie małemu testowi technicznemu. Geometrię i scoring oparto na `smoke_test`; użytkownik nie określił ich jako parametrów eksperymentu.

| Element | Ustawienie robocze |
| --- | --- |
| Wiązka | Monoenergetyczna, punktowa, bez rozbieżności; domyślna waga primary 1 |
| Położenie i kierunek | `(0, 0, -1)` cm w próżni, kierunek `+z` |
| Obiekt | Blok predefiniowanego ołowiu `LEAD`, gęstość 11,350 g/cm³: `x, y = -5…5 cm`, `z = 0…10 cm` |
| Otoczenie | Próżnia w kuli o promieniu 100 cm; powłoka `BLCKHOLE` do promienia 100000 cm |
| Fizyka | `DEFAULTS PRECISIO`, bez dodatkowych kart zmieniających progi i procesy |
| Scoring | `USRBIN ENERGY`, typ 10, siatka `31 × 31 × 30` pokrywająca blok ołowiu (pierwszy przebieg: `21 × 21 × 20`) |
| Wyjście scoringu | Binarne, jednostka 21, detektor `EDEP` |
| Statystyka | 10 000 historii w bieżącym przebiegu technicznym (pierwszy przebieg: 1000) |
| Generator | Nowy przebieg używa identyfikatora sekwencji `7654321` |

`LEAD` jest materiałem predefiniowanym; nie wymaga osobnej karty `MATERIAL`. Przyjętą gęstość podaje [tabela materiałów CERN](https://flukafiles.web.cern.ch/manual/chapters/particle_and_material_codes/pre-defined_materials.html).

Wymiary bloku są przykładem. Nie zakładamy, że blok zatrzyma całą wiązkę lub pochłonie całą jej energię. Zanim powstanie model docelowy, trzeba ustalić geometrię, rzeczywisty profil i rozrzut energii wiązki, mierzoną wielkość oraz normalizację. Roboczo zapisujemy mapę depozycji energii w ołowiu. Użytkownik nie wskazał konkretnej reakcji izotopowej; ustawienia transportu, wymagane procesy i ewentualny scoring produktów reakcji dobierzemy po określeniu celu.

`PRECISIO` włącza transport elektromagnetyczny. `DEFAULTS` znajduje się przed `FREE` i zachowuje pozycję SDUM w kolumnie 71; kolejne karty podają sześć pól WHAT. Źródło: [CERN — DEFAULTS](https://flukafiles.web.cern.ch/manual/chapters/description_input/description_options/defaults.html).

## Odczyt przyszłych wyników

Typ 10 rozdziela depozycję między komórki przecinane przez krok cząstki. Wynik `ENERGY` ma jednostkę **GeV/cm³ na jednostkę wagi primary**, tutaj na jeden elektron źródła. Nie dzielimy go ponownie przez liczbę historii ani objętość komórki. Średnia energia zdeponowana w bloku na elektron to suma wartości komórek pomnożonych przez ich objętość `(10/21) × (10/21) × 0,5 cm³`. Ten scoring nie daje bezpośrednio dawki w Gy. Dane należy przetwarzać narzędziami FLUKA/Flair właściwymi dla USRBIN. Źródło: [CERN — USRBIN](https://flukafiles.web.cern.ch/manual/chapters/description_input/description_options/usrbin.html).

1000 historii służy sprawdzeniu działania; mapa może zawierać duży szum i zera. Jeden cykl nie daje oceny błędu między cyklami. Powtórzenie identycznego modelu i stanu generatora nie daje niezależnej statystyki.

## Przygotowanie w Windows

W PowerShell otwartym w katalogu głównym projektu:

```powershell
.\fluka.cmd prepare electron_500mev
```

Komenda tworzy nową kopię wejść w `runs/`; nie uruchamia symulacji. Po instalacji sprawdzimy geometrię w Flair, następnie wykonamy jeden cykl przez WSL zgodnie z [instrukcją Windows](../../docs/windows.md). Wymagany będzie przegląd `.out`, `.err`, logów, liczby zakończonych historii i scoringu. Przed większą serią ustalimy statystykę i kryteria akceptacji.

Karty sprawdzono według [manuala FLUKA.CERN 4-5.2](https://flukafiles.web.cern.ch/manual/index.html), 2026-09-24. Po instalacji należy sprawdzić zgodność z manualem zainstalowanej wersji.

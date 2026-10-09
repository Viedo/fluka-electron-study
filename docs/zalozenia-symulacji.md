# Założenia symulacji

Status: **źródło, ołów i wodny cel scoringu ustalone dla wariantu technicznego; brak pomiaru referencyjnego i walidacji fizycznej**.

Użytkownik wskazał roboczo **wiązkę elektronów o energii 0,5 GeV (500 MeV)** i oddziaływanie z **ołowiem**. Interpretacja energii jako kinetycznej jest jawnym założeniem modelu; nie należy traktować liczby 0,5 jako pędu w GeV/c.

Przypadek `electron_500mev` jest przykładem technicznym opartym na tych ustaleniach. Dla umożliwienia pierwszego testu przyjmujemy blok Pb 10 × 10 × 10 cm, wiązkę punktową monoenergetyczną i mapę depozycji energii. Wymiary, rozrzut wiązki, otoczenie, siatka i statystyka nie pochodzą od użytkownika i pozostają do zmiany. Cel naukowy i kryteria walidacji nie są jeszcze określone.

`smoke_test` jest osobnym testem technicznym: fotony o energii 1 MeV w wodzie, 1000 historii na cykl. Jego parametry nie określają celu docelowej symulacji. Przypadek `electron_500mev` uruchomiono technicznie dla 1000 historii; większy przebieg z siatką 31×31×30 i 10 000 historii jest przygotowywany jako krok zwiększający szczegółowość, nie jako zatwierdzony model docelowy.

Osobny wariant `electron_wall_water` odpowiada aktualnemu pytaniu o dawkę pochłoniętą w wodzie 1 m za tylną powierzchnią 10-centymetrowego bloku Pb. Przyjęto fantom 10×10×10 cm z siatką 1 cm, 20 pC na paczkę, poprzeczne sigma 1 mm i czasowy FWHM 100 ns. Energia pozostaje monoenergetyczna 500 MeV; rozbieżności kątowej nie dodano, bo jej wartości nie są znane. Są to parametry wariantu technicznego, nie pełne dane rzeczywistego źródła. Punkt odniesienia pomiarowego nadal nie jest dostępny.

Wpisuj jednostkę przy każdej wielkości. Wartość nieznaną oznacz jako „do ustalenia”, a wartość przyjętą roboczo jako „założenie”.

| Obszar | Informacje do uzupełnienia |
| --- | --- |
| Cel | Dla wariantu `electron_wall_water`: jaka jest dawka pochłonięta w wodnym fantomie 1 m za ołowiem? |
| Punkt odniesienia | Brak pomiaru lub uzgodnionego benchmarku; wynik nie jest walidacją osłony. |
| Źródło | Roboczo elektrony e−, zgodnie ze wskazaniem użytkownika. |
| Energia | 0,5 GeV = 500 MeV. Robocza interpretacja: energia kinetyczna; w karcie BEAM wartość −0.5. |
| Widmo | Do ustalenia; przykład techniczny jest monoenergetyczny, bez rozrzutu energii. |
| Położenie źródła | Współrzędne, jednostki, rozmiar oraz kształt obszaru emisji. |
| Kierunek | Kierunek wiązki lub rozkład kątowy; rozbieżność i jej definicja. |
| Geometria | W wariancie wodnym: Pb 10×10×10 cm, fantom wodny 10×10×10 cm, przednia ściana 100 cm za Pb; położenie osiowe centralne. |
| Materiały | Roboczo ołów, wskazany przez użytkownika. W przykładzie materiał predefiniowany LEAD; skład i gęstość rzeczywistej próbki do ustalenia. |
| Otoczenie | Powietrze/próżnia/inne materiały wokół obiektów; uzasadnienie granic modelu. |
| Fizyka transportu | Procesy istotne dla celu, progi transportu i pozostałe ustawienia wymagające uzasadnienia. |
| Scoring | Cel do ustalenia. Roboczo USRBIN ENERGY, mapa depozycji energii w bloku Pb; nie określa jeszcze docelowego pomiaru. |
| Jednostki wyniku | Jednostki surowego scoringu i jednostki oczekiwanego raportu. |
| Normalizacja | Wynik na cząstkę pierwotną czy skalowanie do strumienia, aktywności, czasu lub liczby cząstek? Podaj źródło współczynnika. |
| Niepewność | Oczekiwana niepewność statystyczna w konkretnym obszarze/wielkości; osobno niepewności danych i modelu. |
| Statystyka | Planowana liczba historii na cykl i liczba cykli; dobierz po małym przebiegu. |
| Zasoby | Dostępny CPU, RAM, miejsce na dysku, maksymalny czas jednego przebiegu i całej serii. |
| Kryteria akceptacji | Co musi przejść przegląd geometrii, przebiegu, statystyki i porównania referencyjnego? |
| Rezultaty | Potrzebne tabele, wykresy, przekroje, raporty i format eksportu. |

## Rejestr decyzji

| Data | Decyzja / założenie | Uzasadnienie lub źródło | Co wymaga sprawdzenia |
| --- | --- | --- | --- |
| 2026-09-24 | Wiązka elektronów, energia 0,5 GeV | Wstępna deklaracja użytkownika | Interpretacja kinetyczna oraz rozrzut energii i geometria wiązki |
| 2026-09-24 | Oddziaływanie z ołowiem | Użytkownik: „możesz zakładać reakcję z ołowiem” | Wymiary, skład próbki, otoczenie i cel wyniku |
| 2026-09-24 | Testowy blok 10 × 10 × 10 cm, wiązka punktowa, USRBIN ENERGY, 1000 historii | Założenie techniczne do pierwszego sprawdzenia instalacji | Geometria docelowa, progi i procesy transportu, wystarczająca statystyka |
| 2026-10-09 | Siatka 31×31×30 i 10 000 historii; nowy seed 7654321 | Techniczny krok zwiększający rozdzielczość i statystykę na prośbę użytkownika | Czas obliczeń, ostrzeżenie BLCCRE, niepewność oraz cel i parametry fizyczne |
| 2026-10-09 | Dawka pochłonięta w fantomie wody 10×10×10 cm, 1 m za Pb; sigma wiązki 1 mm, 20 pC, FWHM 100 ns; cztery cykle po 25 000 historii | Uzgodnione dla osobnego wariantu `electron_wall_water`; energia monoenergetyczna 500 MeV | Brak zmierzonej rozbieżności kątowej, rozrzutu energii i punktu odniesienia; sprawdzić błędy koszyków i ostrzeżenia |

## Zasady pracy z Codex

- Opisuj żądaną zmianę i jej cel, np. „zwiększ grubość osłony z … cm do … cm i porównaj …”.
- Każda wartość robocza pozostaje oznaczona do czasu zatwierdzenia jej podstawy fizycznej.
- Rozdzielamy poprawność składni, poprawne zakończenie obliczeń i potwierdzenie wiarygodności modelu. Sam brak błędu programu nie potwierdza poprawności fizycznej.
- Przed większą serią aktualizujemy ten formularz i zapisujemy parametry wariantów, aby wyniki dało się odtworzyć.

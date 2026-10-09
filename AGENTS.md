# Praca z projektem FLUKA

- Rozmawiaj z użytkownikiem po polsku. Czytaj README.md i docs/zalozenia-symulacji.md przed zmianą modelu.
- To projekt FLUKA.CERN. Korzystaj z dokumentacji fluka.cern i manuala odpowiadającego zainstalowanej wersji. Nie mieszaj instrukcji różnych dystrybucji FLUKA.
- Stan początkowy: program jeszcze niedostępny, WSL niezainstalowany. Zweryfikuj stan środowiska przed uruchomieniem; nie traktuj tego opisu jako aktualnej diagnostyki na zawsze.
- Przypadek cases/smoke_test służy tylko sprawdzeniu instalacji. Nie jest modelem docelowego eksperymentu ani zwalidowanym benchmarkiem.
- Aktualny kierunek: elektrony 0,5 GeV (500 MeV) oddziałujące z ołowiem, roboczo wskazane przez użytkownika. cases/electron_500mev to techniczny punkt wyjścia. Interpretacja energii kinetycznej, blok Pb 10 × 10 × 10 cm, wiązka punktowa i mapa depozycji energii są opisanymi założeniami; cel końcowy nie jest jeszcze ustalony.
- Źródła modeli przechowuj w cases/<nazwa>/input.inp. Nazwy przypadków: litera, potem litery/cyfry/podkreślenia, maksymalnie 32 znaki.
- Powiązane pliki wejściowe umieszczaj wewnątrz katalogu przypadku i używaj ścieżek względnych. Skrypt kopiuje cały katalog. Zewnętrzne zależności, user routines i custom executables wymagają rozszerzenia procedury oraz zapisania ich wersji/hashów.
- Ustal rodzaj cząstek, energię i jej jednostkę, geometrię, materiały, scoring oraz normalizację przed obliczeniami docelowymi. Zapisuj przyjęte założenia; nie wymyślaj parametrów eksperymentu.
- Zachowuj format kart FLUKA. Dla FREE uwzględniaj pozycję wszystkich WHAT i SDUM; geometria ma własny format. Pliki .inp zapisuj w ASCII, LF.
- Podstawowy interfejs w Windows to .\fluka.cmd help/doctor/prepare/status/run/test; szczegóły w docs/windows.md. Zmiany modelu zapisuj w cases/, a każdą próbę przygotuj przez .\fluka.cmd prepare NAZWA. W Linux dostępne są scripts/prepare-run.sh i scripts/run-fluka.sh. Nie zmieniaj polityki AllSigned; nie używamy plików .ps1.
- Uruchomienia z Windows kieruj przez .\fluka.cmd run ID CYKLE do WSL. Konfiguracja config/windows.local.conf zawiera dosłowne WSL_DISTRO i FLUKA_BIN, nie jest skryptem. Bezpośrednie wsl --exec nie wczytuje interaktywnego .bashrc. Nie nadpisuj poprzednich przebiegów ani ich input/, work/, seedów i logów. Dowolny tekst notatki zapisuj w note.txt; nie przekazuj go jako argument .cmd.
- Najpierw przegląd geometrii w Flair i krótki przebieg. Większe serie planuj według uzgodnionych zasobów i celu. Użytkownik może zmienić te ustalenia.
- Zapisuj wersję FLUKA i bibliotek, źródło danych, liczbę historii i cykli, seed oraz komendę. Identyczny seed przy identycznym modelu daje powtórzenie, nie niezależną statystykę.
- Po uruchomieniu sprawdź .out, .err, .log, zakończenie każdego cyklu i scoring. Kod wyjścia 0 i status finished_needs_review nie są walidacją fizyczną.
- Nie przedstawiaj testów skryptów z atrapą rfluka jako uruchomionej symulacji. Jawnie opisuj brak dostępu do FLUKA i niepewność.
- Analizuj wyniki narzędziem FLUKA/Flair właściwym dla scoringu. Zapisuj jednostki, przeliczenia, normalizację na primary oraz niepewność; pojedynczy cykl nie daje oceny błędu między cyklami.
- Raporty zapisuj w reports/, kod analizy w analysis/. Zachowuj połączenie raportu z identyfikatorem przebiegu. Nie dodawaj instalatorów ani dużych wyników do Git.
- Po zmianach skryptów uruchom adekwatne testy techniczne przez .\fluka.cmd test. Test argumentów WSL używa atrapy; nie potwierdza integracji z prawdziwym WSL. Nie instaluj dodatkowego środowiska analizy, dopóki nie będzie potrzebne.

Opis mechanizmu instrukcji: https://learn.chatgpt.com/docs/agent-configuration/agents-md

# Praca nad symulacją

Na początek przygotowujemy przykład techniczny `electron_500mev`: elektrony 500 MeV w ołowiu, 1000 historii na cykl. Wymiary bloku i mapa depozycji energii są roboczymi założeniami, a cel końcowy pozostaje do ustalenia. Przed instalacją FLUKA można przygotowywać pliki i foldery przebiegów; wyników fizycznych jeszcze nie ma.

## 1. Model i geometria

Uzupełnij [założenia symulacji](zalozenia-symulacji.md). Zmiany modelu wprowadzaj w odpowiednim katalogu `cases/`, z opisem jednostek i przyjętych założeń.

Otwórz plik wejściowy w Flair. Sprawdź przekroje, przypisanie materiałów, położenie i kierunek źródła oraz obszary scoringu. Użyj dostępnych kontroli geometrii i sprawdź, czy nie ma luk, nakładających się regionów ani niezamierzonych obszarów. Zapisz uwagi z przeglądu. Sama wizualizacja nie zastępuje kontroli komunikatów podczas transportu cząstek.

## 2. Osobny folder przebiegu

Już przed instalacją WSL, w PowerShell otwartym w głównym folderze projektu, uruchom przygotowanie przez dostępny Git Bash:

```powershell
.\fluka.cmd prepare electron_500mev
```

W terminalu Git Bash lub, po instalacji, w terminalu Ubuntu użyj:

```bash
bash scripts/prepare-run.sh electron_500mev
```

Lista przygotowanych przebiegów jest dostępna przez `.\fluka.cmd status`. Dodatkowy opis zapisz w pliku `note.txt` wewnątrz wybranego przebiegu.

Skrypt tworzy nowy folder w `runs/` i zapisuje manifest JSON z podstawowymi metadanymi oraz sumą SHA256 głównego wejścia. `inputs.sha256` zawiera pełną listę sum wszystkich plików w `input/` i `work/`. Zmiana, dodanie lub usunięcie pliku zatrzyma start przebiegu. Zachowaj wyświetloną nazwę katalogu. Podfolder `input/` przechowuje niezmienianą kopię całego przypadku, a `work/` zawiera kopię roboczą i wyniki FLUKA. Główny plik wejściowy nazywa się `input.inp`. `tooling/` archiwizuje skrypty przygotowania i wykonania. Kolejny wariant przygotuj w `cases/` i skopiuj do nowego przebiegu.

W katalogu przebiegu znajdziesz też `status.txt`. Przy rozpoczęciu obliczeń powstaną log runnera `console.log` oraz `execution.txt` opisujący parametry i środowisko uruchomienia.

## 3. Mały przebieg

Po instalacji i skonfigurowaniu `config/windows.local.conf` uruchom z PowerShell:

```powershell
.\fluka.cmd doctor
.\fluka.cmd run ID 1
```

Zastąp `ID` nazwą przebiegu z `status`. Polecenie przejdzie do właściwego katalogu i wywoła runner we wskazanej dystrybucji WSL.

Alternatywnie w terminalu Ubuntu wykonaj poniższe polecenia. Zastąp `NAZWA_KATALOGU_PRZEBIEGU` nazwą utworzoną przez skrypt. Ścieżka Git Bash `/c/Users/...` odpowiada w WSL `/mnt/c/Users/...`:

```bash
cd /mnt/c/Users/roman.panas/Desktop/FLUKA
bash scripts/run-fluka.sh 'runs/NAZWA_KATALOGU_PRZEBIEGU' 1
```

Ostatni argument jest liczbą cykli; domyślnie wynosi 1. Runner wyszukuje `rfluka` w `PATH` lub korzysta z katalogu wskazanego przez `FLUKA_BIN`. Git Bash służy w tym projekcie do przygotowania plików i testów automatyzacji; właściwe obliczenia FLUKA uruchamiamy w WSL.

Odpowiednikiem pojedynczego cyklu z terminala, już w katalogu `work/` zawierającym wejście, jest:

```bash
rfluka -N 0 -M 1 input.inp
```

`-N` oznacza numer ostatniego ukończonego cyklu, a `-M` numer ostatniego cyklu do wykonania. FLUKA wykonuje cykle kolejno; zwiększenie tej liczby nie uruchamia obliczeń na wielu rdzeniach. Cykl obejmuje liczbę historii określoną w wejściu, z uwzględnieniem ewentualnego limitu czasu. [Dokumentacja CERN](https://fluka.cern/documentation/running/fluka-command-line).

## 4. Przegląd zakończenia

Status runnera `finished_needs_review` oznacza zakończenie wymagające oceny. Dla przebiegu z plikiem `input001_fort.21` runner automatycznie generuje pięć wykresów EDEP i kopiuje je do `~/Desktop/FLUKA-wyniki/<run_id>/`. Dla przypadku `electron_wall`, jeśli powstanie też `input001_fort.22`, generuje ponadto mapę dawki i widmo fotonów. Przypadek `electron_wall_water` dodatkowo przetwarza trzywymiarowe rozkłady dawki w wodnym fantomie. Katalog bazowy można ustawić przez `FLUKA_DESKTOP_RESULTS_DIR`. Otwórz w `work/` pliki `.out`, `.err` i `.log` z każdego cyklu. Sprawdź komunikaty o błędach, geometrii i przerwaniu obliczeń, faktyczną liczbę przetransportowanych historii oraz obecność oczekiwanych wyników scoringu.

Dla wejścia `input.inp` pierwszy cykl tworzy m.in. `input001.out`, `input001.err`, `input001.log`; `raninput001` przechowuje stan generatora dla kolejnego cyklu. Nazwy bazują na nazwie wejścia. Zachowaj pliki `ran…`, oryginalne wyniki oraz manifest. [Opis plików i cykli CERN](https://fluka.cern/documentation/running/fluka-command-line).

Do folderu przebiegu dodaj notatkę z datą, wersją FLUKA i bibliotek, oceną komunikatów oraz decyzją o dalszej pracy. Gdy test nie przejdzie, zachowaj folder i diagnozę, popraw wejście w `cases/`, a kolejną próbę przygotuj w nowym folderze.

## 5. Statystyka i serie

Po pozytywnym przeglądzie małego testu oszacuj czas oraz rozmiar wyników. Zaplanuj liczbę historii i wiele cykli odpowiednio do celu i wymaganej niepewności. Jeden krótki cykl jest testem działania, a do oceny błędu statystycznego scoringu potrzebna jest analiza wielu cykli. [Zasada oceny błędu w FLUKA](https://fluka.cern/documentation/running/fluka-command-line).

Każdy wariant geometrii, źródła lub ustawień fizycznych otrzymuje osobny folder przebiegu. Nie zmieniaj wejścia w trakcie obliczeń. Nie łącz cykli pochodzących z różnych konfiguracji. Ponowne uruchomienie identycznego wejścia z tym samym seedem nie daje niezależnej próby statystycznej; planując niezależne przebiegi, jawnie zapisz i sprawdź ich stany początkowe generatora.

Kontynuację istniejącego przebiegu zaplanuj osobno po sprawdzeniu ukończonych cykli i zachowanych stanów generatora. Runner projektu służy do nowych przebiegów; nie należy traktować ponownego wywołania jako automatycznego wznowienia.

## 6. Przetwarzanie i ocena wyniku

Dobierz natywne narzędzie FLUKA/Flair do użytego scoringu. Dla wielu cykli łącz pliki USRBIN narzędziem `usbsuw`, a USRTRACK narzędziem `ustsuw`; nie traktuj pojedynczego cyklu jako estymacji błędu między cyklami. Zachowaj surowe pliki wszystkich cykli, polecenia, wersje narzędzi i raporty. Pliki scalone, tabele i wykresy zapisuj oddzielnie od surowych wyników; nazwij je tak, aby wskazywały przypadek i zakres cykli.

Przed przeliczeniem jednostek sprawdź definicję danego scoringu: jego surową jednostkę, normowanie na historię, sposób uwzględnienia objętości oraz szerokości przedziałów energii. Zanotuj każdy współczynnik skali i jego źródło. Nie stosuj jednej formuły normalizacji do wszystkich typów detektorów.

Oceń statystykę w obszarze istotnym dla celu, stabilność wyniku przy zwiększeniu liczby historii oraz zgodność z punktem odniesienia. Brak zliczeń nie dowodzi braku efektu fizycznego. Większa liczba historii poprawia statystykę, ale nie usuwa błędów geometrii, danych źródła ani założeń modelu.

Raport powinien podawać model, parametry źródła, materiały, liczbę ukończonych historii i cykli, jednostki, normalizację, niepewności oraz ograniczenia interpretacji. Określenie wyniku jako zweryfikowanego wymaga spełnienia zapisanych kryteriów, a nie samego zakończenia procesu.

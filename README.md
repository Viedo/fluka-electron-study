# Projekt FLUKA na Windows

Projekt obsługujemy z **PowerShell w Windows**, a właściwe obliczenia FLUKA.CERN będą wykonywane w **Ubuntu przez WSL**. Codex pracuje w tym folderze i korzysta z tych samych plików oraz poleceń.

**Aktualny kierunek modelu:** wiązka elektronów o energii **0,5 GeV = 500 MeV**, oddziałująca z **ołowiem**. Interpretujemy energię roboczo jako kinetyczną. Wymiary obiektu, parametry wiązki i cel obliczeń pozostają do ustalenia.

**Stan na 2026-10-09:** w maszynie AlmaLinux 9.8 zainstalowano FLUKA 4-5.2, bibliotekę neutronową JEFF-3.3 i Flair 3.4-5.4. Przypadek `electron_500mev` uruchomiono technicznie dla 1000 historii, a następnie dla 10 000 historii na siatce EDEP 31×31×30. Drugi przebieg (`20261009T063202Z_electron_500mev_iJ0KXKBU`) ma mapę centralną, trzy mapy poprzeczne, profile podłużny i promieniowy oraz widok 3D. Dla wariantu `electron_wall_water` przygotowano przebieg z planem 4×25 000 historii i fantomem wodnym 10 cm, którego przednia powierzchnia znajduje się 1 m za ołowiem; na żądanie użytkownika zatrzymano go po 50 000 historiach w dwóch pełnych cyklach i 15 419 historiach trzeciego cyklu (`20261009T090627Z_electron_wall_water_TrYgQ1Q5`). Przebieg wodny jest nieukończony: nie scalono wyników ani nie wyznaczono końcowej dawki. Żaden z tych przypadków nie jest walidacją fizyczną; ostrzeżenia BLCCRE wymagają przeglądu, a błędy statystyczne należy ocenić przed interpretacją.

Folder jest współdzielony przez VMware (`/mnt/hgfs`), gdzie system plików nie obsługuje dowiązań wymaganych przez `rfluka`. Oba obliczenia wykonano na lokalnym systemie plików Linuksa, a ich artefakty skopiowano do katalogów przebiegów. Dotychczasowe przebiegi zachowano.

Wykresy wyników EDEP są dostępne również na pulpicie w `~/Desktop/FLUKA-wyniki/<ID_przebiegu>/`. Runner kopiuje je tam automatycznie po udanym przebiegu z plikiem USRBIN `input001_fort.21`.

Osobny przypadek `electron_wall` modeluje technicznie 20 pC elektronów 500 MeV na bloku Pb 10 cm oraz widmo fotonów i dawkę w powietrzu 20 cm za blokiem. Wymaga osobnego przeglądu i nie jest walidacją osłony.

## Zacznij tutaj

W PowerShell otwartym w folderze `C:\Users\roman.panas\Desktop\FLUKA`:

```powershell
.\fluka.cmd help
.\fluka.cmd doctor
.\fluka.cmd status
```

`doctor` zwróci kod 1, dopóki środowisko obliczeniowe nie będzie gotowe. Obecnie poprawnie wykrywa brak WSL. Niczego nie instaluje. Przeczytaj [instrukcję Windows](docs/windows.md) i [instalację WSL/FLUKA](docs/instalacja.md).

## Dostępne polecenia

| Polecenie | Działanie |
| --- | --- |
| `.\fluka.cmd prepare electron_500mev` | Tworzy nowy katalog z kopiami wejść i sumami SHA256, bez obliczeń |
| `.\fluka.cmd status` | Wyświetla identyfikatory i stan przebiegów |
| `.\fluka.cmd status ID` | Pokazuje szczegóły konkretnego przebiegu |
| `.\fluka.cmd doctor` | Sprawdza Git Bash, WSL i narzędzia w wybranej dystrybucji |
| `.\fluka.cmd run ID 1` | Po instalacji wykonuje jeden cykl FLUKA w WSL |
| `.\fluka.cmd test` | Sprawdza automatyzację za pomocą atrap FLUKA i WSL |

`ID` zastępujemy rzeczywistą nazwą katalogu z `status`. Domyślnie wybierana jest dystrybucja `Ubuntu`. Katalog FLUKA i ewentualną inną dystrybucję wskaż w [lokalnej konfiguracji](docs/windows.md#lokalna-konfiguracja), na podstawie `config/windows.example.conf`.

Polecenia korzystają z dostępnego Git Bash. Nie wymagają Pythona ani skryptów PowerShell; wymuszona polityka Windows `AllSigned` pozostaje bez zmian. Dowolne notatki wpisujemy do `note.txt` wewnątrz przebiegu, zamiast przekazywać je przez CMD.

W Ubuntu można też używać bezpośrednio `bash scripts/prepare-run.sh electron_500mev` i `bash scripts/run-fluka.sh runs/ID 1`.

## Organizacja projektu

| Folder / plik | Zawartość |
| --- | --- |
| `AGENTS.md` | Instrukcje projektu dla Codexa |
| `cases/electron_500mev/` | Roboczy przykład elektronów 500 MeV z testowym blokiem ołowiu; geometria nie jest jeszcze modelem eksperymentu |
| `cases/electron_wall/` | Techniczny model widma fotonów i dawki w powietrzu za ołowiem, z jawnymi założeniami 20 pC i 10 cm Pb |
| `cases/electron_wall_study/` | Wariant czterech cykli z mapami dawki w trzech odległościach i widmami kilku składników promieniowania |
| `cases/electron_wall_water/` | Osobny wariant z dawką pochłoniętą w 10 cm fantomie wodnym, 1 m za ołowiem |
| `cases/smoke_test/` | Wcześniejszy test instalacji: fotony 1 MeV i woda |
| `cases/<nazwa>/input.inp` | Wejścia modeli i lokalne pliki zależne |
| `runs/` | Kopie wejść, wyniki, seedy, logi, metadane i użyte skrypty |
| `config/`, `scripts/` | Konfiguracja Windows/WSL, obsługa poleceń i testy |
| `analysis/`, `reports/` | Analiza, wykresy i raporty |
| `data/`, `installers/` | Dane pomocnicze i lokalnie pobrane paczki CERN |
| `docs/` | Instalacja, założenia modelu, workflow i stan weryfikacji |

Każde przygotowanie tworzy nowy przebieg. Przed startem porównujemy pełną zawartość obu kopii wejść; dodanie, usunięcie lub zmiana pliku wymaga ponownego przygotowania. Po rozpoczęciu katalog jest chroniony przed ponownym startem. Wznowienia, custom executables i klastry nie są jeszcze obsługiwane.

Surowe wyniki i instalatory są pomijane przez Git. Archiwizujemy cały katalog przebiegu osobno. Status `finished_needs_review` oznacza zakończenie procesu i obecność `.out`; wymaga jeszcze przeglądu logów, scoringu i poprawności fizycznej.

W repozytorium znajdują się wybrane, wygenerowane wykresy, tabele CSV i podsumowanie z przebiegów `20261009T063202Z_electron_500mev_iJ0KXKBU` oraz `20261009T070639Z_electron_wall_n5xWPPVP`. Surowe pliki FLUKA, w tym nieukończony przebieg wodny, pozostają wykluczone.

## Następne kroki

1. W razie potrzeby skonfigurujemy Windows/WSL zgodnie z istniejącym wrapperem; bieżąca instalacja działa bezpośrednio w maszynie AlmaLinux.
2. Sprawdzamy geometrię i scoring we Flair oraz komunikaty z przebiegu.
3. Uzupełniamy [założenia właściwej symulacji](docs/zalozenia-symulacji.md): parametry wiązki elektronów, obiekt, materiały, geometria i mierzona wielkość.
4. Dopiero po uzgodnieniu celu planujemy statystykę większą niż techniczne 1000 historii.

Przykładowa prośba do Codexa:

> Przeczytaj instrukcje projektu, sprawdź środowisko przez fluka.cmd doctor i przygotuj model wiązki elektronów 500 MeV na podstawie uzgodnionych założeń.

[Testy automatyzacji](docs/weryfikacja.md) nie zastępują pierwszego uruchomienia w rzeczywistym WSL/FLUKA ani walidacji fizycznej przykładu.

Źródła: [CERN — FLUKA na Windows/WSL](https://fluka.cern/documentation/installation/fluka-flair-windows-wsl), [Microsoft — instalacja WSL](https://learn.microsoft.com/en-us/windows/wsl/install), [CERN — rfluka](https://fluka.cern/documentation/running/fluka-command-line).

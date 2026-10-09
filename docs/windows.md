# Praca z FLUKA na Windows

Projekt obsługujemy z PowerShell w Windows. Pliki modeli i wyniki są w tym samym folderze widocznym dla Codexa. FLUKA oraz Flair będą działać w Ubuntu w WSL, zgodnie z [instrukcją CERN](https://fluka.cern/documentation/installation/fluka-flair-windows-wsl).

Stan sprawdzony 24.09.2026: WSL nie jest jeszcze zainstalowany, nie uruchomiono prawdziwej symulacji FLUKA. Po zmianach środowiska aktualny stan sprawdza polecenie `doctor`.

## Polecenia projektu

Otwórz PowerShell w folderze `C:\Users\roman.panas\Desktop\FLUKA`:

```powershell
.\fluka.cmd help
.\fluka.cmd doctor
.\fluka.cmd prepare electron_500mev
.\fluka.cmd status
.\fluka.cmd test
```

| Polecenie | Co robi |
| --- | --- |
| `help` | Pokazuje dostępne polecenia i argumenty. |
| `doctor` | Sprawdza narzędzia i gotowość środowiska; nie instaluje programów. |
| `prepare electron_500mev` | Tworzy nowy przebieg w `runs/`: kopie wejścia, sumy SHA256 i metadane. Nie rozpoczyna obliczeń. Notatkę można zapisać w pliku `note.txt` przebiegu. |
| `status` | Pokazuje zapisane przebiegi i ich stan. Dodanie `ID` wyświetla szczegóły jednego przebiegu. |
| `run ID 1` | Po instalacji uruchamia wskazany przebieg w WSL przez jeden cykl. `ID` to nazwa folderu przebiegu. |
| `test` | Sprawdza automatyzację z atrapą programu; nie wykonuje symulacji FLUKA. |

Przygotowanie plików i testy mogą działać już teraz dzięki Git Bash. Do obliczeń potrzebne będą WSL, Ubuntu i instalacja FLUKA. Skrypty nie wymagają Pythona w Windows. Lokalna polityka `MachinePolicy: AllSigned` pozostaje bez zmian; obsługa projektu przez `.cmd` i Git Bash nie wymaga wykonywania plików `.ps1`.

Do `fluka.cmd` przekazujemy tylko nazwy poleceń, przypadków, wygenerowane identyfikatory i liczbę cykli. Dowolny tekst wpisujemy bezpośrednio do `note.txt`, ponieważ CMD interpretuje znaki specjalne, np. `&`, także w części wywołań z PowerShell. Nazwy przypadków zawierają litery, cyfry i podkreślenia; pierwszym znakiem jest litera.

## Instalacja, gdy będziemy gotowi

Skrypt przygotowawczy nie instaluje WSL. Następnym krokiem będzie ręczne `wsl --install -d Ubuntu`, ponieważ instalacja obejmuje restart oraz utworzenie konta użytkownika Linux.

1. Zainstaluj WSL i Ubuntu według [instrukcji instalacji projektu](instalacja.md). Microsoft opisuje `wsl --install` dla Windows 10 od wersji 2004, build 19041, oraz Windows 11. Polecenie uruchamia się w PowerShell jako administrator; instalacja może wymagać restartu. Nowe dystrybucje korzystają domyślnie z WSL 2. Przy pierwszym starcie Ubuntu trzeba utworzyć użytkownika Linux. [Źródło: Microsoft](https://learn.microsoft.com/en-us/windows/wsl/install).
2. Sprawdź nazwę i wersję dystrybucji:

   ```powershell
   wsl --list --verbose
   ```

3. Po uzyskaniu dostępu CERN pobierz aktualny pakiet FLUKA dla Ubuntu oraz właściwą bibliotekę neutronową. Zainstaluj również Flair, który posłuży do przeglądu geometrii. Szczegóły i odnośniki są w [instalacja.md](instalacja.md).
4. Ustaw lokalną konfigurację opisaną poniżej i uruchom `.\fluka.cmd doctor`, aby sprawdzić dostępność środowiska z poziomu Windows.

## Lokalna konfiguracja

Opcjonalny `config/windows.local.conf` wskazuje dystrybucję WSL i katalog FLUKA. Utwórz go na podstawie wzoru:

```powershell
Copy-Item config/windows.example.conf config/windows.local.conf
```

Po instalacji wpisz rzeczywiste wartości w tym pliku, na przykład:

```text
WSL_DISTRO=Ubuntu
FLUKA_BIN=/sciezka/do/fluka/bin
```

`FLUKA_BIN` to katalog **w Linux** zawierający `rfluka`; podana ścieżka jest wzorem do zastąpienia. Jawne wskazanie katalogu jest zalecane, ponieważ uruchomienie z Windows nie wczytuje interaktywnego `.bashrc`. Puste `FLUKA_BIN` oznacza wyszukanie `rfluka` w `PATH` procesu WSL. Domyślnie wybierane jest `Ubuntu`; puste `WSL_DISTRO` oznacza domyślną dystrybucję WSL.

Wpisuj po jednym `KLUCZ=wartość` w wierszu, bez cudzysłowów wokół wartości. Spacje wewnątrz wartości są obsługiwane. Komentarz zajmuje osobny wiersz zaczynający się od `#`. Plik jest odczytywany jako dane i nie wykonuje poleceń powłoki; nie używaj `export` ani zmiennych typu `$HOME`. Lokalne ustawienia nie trafiają do Git.

## Pierwszy rzeczywisty przebieg

Otwórz `cases/electron_500mev/input.inp` w Flair i sprawdź geometrię. To wyłącznie test instalacji; parametry właściwego eksperymentu ustalimy w [założeniach symulacji](zalozenia-symulacji.md).

Przygotuj nowy przebieg i skopiuj wypisany identyfikator:

```powershell
.\fluka.cmd prepare electron_500mev
.\fluka.cmd status
.\fluka.cmd run ID 1
```

`ID` w ostatniej linii należy zastąpić rzeczywistą nazwą katalogu w `runs/`. Pominięcie liczby cykli oznacza jeden cykl. Każde kolejne uruchomienie wymaga nowego przebiegu; stare wejścia, seedy i wyniki pozostają zapisane.

Po zakończeniu sprawdzamy pliki `.out`, `.err`, `.log` i scoring zgodnie z [workflow.md](workflow.md). Status `finished_needs_review` nie potwierdza poprawności fizycznej. Pojedynczy cykl służy sprawdzeniu działania i nie daje oceny niepewności między cyklami.

## Ścieżki i typowe problemy

Ten sam katalog ma różne zapisy:

| Środowisko | Ścieżka projektu |
| --- | --- |
| Windows | `C:\Users\roman.panas\Desktop\FLUKA` |
| Git Bash | `/c/Users/roman.panas/Desktop/FLUKA` |
| Ubuntu w WSL | `/mnt/c/Users/roman.panas/Desktop/FLUKA` |

WSL udostępnia pliki Windows przez `/mnt/c`. Na początek zachowujemy jeden folder projektu. Przy większych obliczeniach możemy przenieść projekt lub obszar wyników do systemu plików Linux, aby ograniczyć koszt operacji na plikach; wymaga to ustalenia miejsca danych i aktualizacji procedury przebiegów. [Źródło: Microsoft — systemy plików](https://learn.microsoft.com/en-us/windows/wsl/filesystems).

- **Jest `wsl.exe`, ale `doctor` zgłasza brak WSL lub Ubuntu:** obecność polecenia nie potwierdza ukończonej instalacji. Sprawdź `wsl --status` i `wsl --list --verbose`; po instalacji może być potrzebny restart i pierwszy start Ubuntu.
- **`rfluka` działa w terminalu Ubuntu, ale nie z Windows:** ustaw rzeczywisty katalog `rfluka` w `FLUKA_BIN` w `config/windows.local.conf`. Nie kopiuj ścieżki Windows do tego ustawienia, które dotyczy systemu Linux.
- **Flair nie wyświetla okna:** sprawdź integrację aplikacji graficznych WSL oraz kroki z instrukcji CERN. Działający terminal FLUKA nie potwierdza działania GUI.
- **Przebieg jest zablokowany albo zakończył się błędem:** zachowaj katalog i sprawdź logi. Popraw źródło w `cases/`, następnie wykonaj `prepare` dla nowego przebiegu.

Dokumentację zewnętrzną sprawdzono 24.09.2026. Po instalacji podstawą do ustawień fizyki i interpretacji wyników będzie manual dokładnie tej wersji FLUKA.CERN, którą zainstalujemy.

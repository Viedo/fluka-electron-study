# Instalacja środowiska

Stan sprawdzony 24.09.2026: w tym systemie nie ma jeszcze WSL; polecenie `py -3` nie znalazło zainstalowanego Pythona. Dostępny Git Bash pozwala już przygotowywać foldery przebiegów i testować automatyzację. Uruchomienie FLUKA będzie wymagało Linuxa w WSL. Przygotowanie projektu nie instaluje żadnego programu, a skrypty startowe nie wymagają Pythona.

Lokalna polityka podpisów `MachinePolicy: AllSigned` blokuje niepodpisane skrypty PowerShell. Polityka pozostaje bez zmian. Obsługujemy projekt przez `fluka.cmd` i Git Bash. Szczegóły: [praca na Windows](windows.md).

Już teraz, w PowerShell otwartym w głównym folderze projektu, możesz przygotować przebieg przez Git Bash:

```powershell
.\fluka.cmd prepare electron_500mev
```

W terminalu Git Bash, a po instalacji również w Ubuntu, odpowiednikiem jest:

```bash
bash scripts/prepare-run.sh electron_500mev
```

Git Bash wyświetla ścieżki dysku C jako `/c/...`, a WSL jako `/mnt/c/...`. Do późniejszego uruchomienia w Ubuntu użyj nazwy folderu `runs/ID` zgodnie z [workflow.md](workflow.md). Git Bash służy tutaj do przygotowania plików i testów automatyzacji; symulacje uruchamiamy w WSL.

## 1. Ubuntu w WSL

W terminalu PowerShell uruchomionym jako administrator wykonaj:

```powershell
wsl --install -d Ubuntu
```

Dokończ instrukcje instalatora, w tym restart Windows, jeśli zostanie wymagany. Uruchom Ubuntu i utwórz użytkownika Linux. Następnie w PowerShell sprawdź:

```powershell
wsl --list --verbose
```

Folder projektu jest dostępny w Ubuntu pod ścieżką:

```bash
cd /mnt/c/Users/roman.panas/Desktop/FLUKA
```

CERN opisuje przygotowanie WSL oraz instalację zależności i Flair za pomocą skryptu `setup_wsl.sh`. Skorzystaj z odnośnika do skryptu w [oficjalnej instrukcji CERN](https://fluka.cern/documentation/installation/fluka-flair-windows-wsl). Po pobraniu i rozpakowaniu archiwum wejdź w Ubuntu do folderu zawierającego ten plik, przeczytaj go i uruchom:

```bash
sudo ./setup_wsl.sh
```

Flair posłuży do oglądania i sprawdzania geometrii. Same przebiegi projektu można wykonywać z terminala.

## 2. FLUKA po otrzymaniu dostępu

Z konta CERN pobierz pakiet FLUKA dla Ubuntu: wariant `gfortran>=9`, 64-bit, `.deb`, oraz domyślną bibliotekę neutronową w formacie `.deb`. Wersję i zgodność pakietów sprawdź przy pobieraniu. Nie zapisuj instalatorów ani danych konta w repozytorium projektu.

W Ubuntu otwórz folder pobranych plików:

```bash
cd /mnt/c/Users/roman.panas/Downloads
```

Zastąp oba opisy w poniższej komendzie **pełnymi nazwami pobranych plików**, łącznie z `.deb`:

```bash
sudo apt install './PELNA_NAZWA_PAKIETU_FLUKA.deb' './PELNA_NAZWA_BIBLIOTEKI_NEUTRONOWEJ.deb'
```

Komenda z nazwami `PELNA_NAZWA_…` jest wzorem i nie zadziała bez ich uzupełnienia. Nie używaj symboli wieloznacznych przy wyborze instalatorów. Powyższy wybór pakietów opisuje [instrukcja instalacji CERN dla Windows/WSL](https://fluka.cern/documentation/installation/fluka-flair-windows-wsl).

## 3. Dostęp do poleceń

W Ubuntu sprawdź:

```bash
command -v rfluka
command -v flair
```

Jeśli `rfluka` nie jest dostępne, ustal rzeczywisty katalog instalacji i zastąp `/sciezka/do/fluka/bin` w tej komendzie:

```bash
export PATH="/sciezka/do/fluka/bin:$PATH"
```

Aby zachować ustawienie, dopisz tę samą linię z rzeczywistą ścieżką do `~/.bashrc`, a następnie wykonaj:

```bash
source ~/.bashrc
command -v rfluka
```

Alternatywnie runner projektu przyjmuje zmienną `FLUKA_BIN` wskazującą katalog z `rfluka`:

```bash
export FLUKA_BIN="/sciezka/do/fluka/bin"
```

Dla polecenia `.\fluka.cmd run` zapisz ten katalog jako `FLUKA_BIN=/sciezka/do/fluka/bin` w `config/windows.local.conf`, zgodnie z [instrukcją Windows](windows.md#lokalna-konfiguracja). Ustawienie `export` w interaktywnym terminalu Ubuntu nie konfiguruje automatycznie wywołania z Windows.

Konfigurację `PATH` wyjaśnia [dokumentacja uruchamiania FLUKA](https://fluka.cern/documentation/running/fluka-command-line). Zapisz rzeczywistą wersję FLUKA i biblioteki danych w dokumentacji pierwszego przebiegu.

## 4. Pierwsze otwarcie

W Ubuntu:

```bash
cd /mnt/c/Users/roman.panas/Desktop/FLUKA
flair
```

Otwórz w Flair wejście z `cases/electron_500mev`, sprawdź geometrię, a następnie wykonaj procedurę z [workflow.md](workflow.md). Ten przykład jest roboczym testem instalacji i wymaga uruchomienia oraz przeglądu wyników.

Na tym etapie nie potrzeba dodatkowych bibliotek Pythona. Dobierzemy je, jeśli analiza wyników będzie tego wymagać.

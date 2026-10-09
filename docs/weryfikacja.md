# Stan weryfikacji — 2026-10-09

## Sprawdzone na tym Windows

- Git Bash jest dostępny. Polecenie listowania dystrybucji zgłasza brak instalacji WSL.
- `MachinePolicy` ma wartość `AllSigned`. Nie zmienialiśmy polityki; obsługa projektu nie wymaga plików `.ps1`.
- Rzeczywiste polecenia `.\fluka.cmd help`, `doctor` i `status` działają z PowerShell. Diagnostyka zwraca kod 1 z informacją o brakującym WSL.
- W maszynie AlmaLinux 9.8 zainstalowano FLUKA 4-5.2, neutronowe dane JEFF-3.3 oraz Flair 3.4-5.4.
- FLUKA poprawnie sparsowała i wykonała przypadek `electron_500mev`: 1000 elektronów w jednym cyklu. Przebieg `20261009T061821Z_electron_500mev_g0d6X60y` ma status `finished_needs_review`; wynik USRBIN został odczytany parserem Flair i zwizualizowany. Nie jest to walidacja fizyczna modelu.
- Wykonano drugi techniczny przebieg `20261009T063202Z_electron_500mev_iJ0KXKBU`: 10 000 historii w jednym cyklu, siatka EDEP 31×31×30, seed 7654321. Zakończył się poprawnie; wejściowe sumy kontrolne są zgodne, plik USRBIN ma 115 558 bajtów. Czas CPU śledzenia primary wyniósł 288.2 s. Status `finished_needs_review` oznacza potrzebę dalszego przeglądu, nie akceptację fizyczną.
- W trakcie uruchomienia wykryto konieczność przełączenia na `FIXED` dla standardowych kart `GEOBEGIN`/`GEOEND`, a następnie powrotu do `FREE`; przypadek poprawiono i ponownie przygotowano. Dwie wcześniejsze nieudane próby zachowano w `runs/`.
- `rfluka` nie może uruchamiać obliczeń bezpośrednio w VMware HGFS (`/mnt/hgfs`), ponieważ udział nie obsługuje dowiązań symbolicznych. Udany przebieg wykonano na lokalnym systemie plików Linuksa, a wyniki i metadane skopiowano do projektu.
- Zegar maszyny wirtualnej jest niespójny z czasem sesji: przebieg dostał identyfikator z datą 2026-10-09, choć sesja rozpoczęła się 2026-10-08. Znaczniki czasu w metadanych przebiegu pochodzą z zegara VM; należy je skorygować przed analizą zależną od czasu.
- Raport FLUKA zawiera ostrzeżenie BLCCRE: dopasowanie nie utrzymało błędu względnego poniżej 1%; maksymalny błąd wyniósł 54.5% przy beta2=0.37014. Wynik wymaga przeglądu przed dalszym użyciem.
- Ostrzeżenie BLCCRE wystąpiło również w drugim przebiegu z 10 000 historiami, więc zwiększenie statystyki go nie rozwiązuje.
- `analysis/plot_usrbin.py` wygenerował z drugiego przebiegu centralny przekrój, trzy mapy poprzeczne w różnych głębokościach, profile podłużny i promieniowy oraz odpowiadające im pliki CSV. Pliki są w `reports/generated/20261009T063202Z_electron_500mev_iJ0KXKBU/`. Skrypt sprawdzono składniowo i uruchomiono na wynikach FLUKA.
- Przebieg `electron_wall` (`20261009T070639Z_electron_wall_n5xWPPVP`) zakończył jeden cykl 100 000 historii w 51 min 6 s. Raport i wybrane wykresy oraz CSV znajdują się w `reports/generated/`; status `finished_needs_review` i ostrzeżenia BLCCRE wymagają dalszej oceny.
- Przebieg wodny `20261009T090627Z_electron_wall_water_TrYgQ1Q5` zatrzymano na żądanie po dwóch pełnych cyklach po 25 000 historii i 15 419 historiach trzeciego cyklu. Czwarty cykl nie został uruchomiony; scoringu nie scalono, więc nie ma końcowego wyniku dawki. Surowe, częściowe pliki przebiegu nie są publikowane.

## Testy automatyzacji

Uruchomienie z PowerShell:

```powershell
.\fluka.cmd test
```

`test-workflow.sh` korzysta z atrapy `rfluka`. Sprawdza przygotowanie i unikalność katalogów, hashe oraz kompletność obu kopii wejść, archiwizację skryptów, ścieżki ze spacjami, nieprawidłowe argumenty, brak programu, stare wyniki, błędy procesu, brak wyników przy kodzie 0, wiele cykli i ochronę przed ponownym startem. Zmiana snapshotu, dodanie/usunięcie zależności i zmiana archiwum skryptu zatrzymują start.

`test-windows.sh` testuje dispatcher z atrapą `wsl.exe`: wyjście UTF-16LE listy dystrybucji, brak WSL/dystrybucji, dosłowne argumenty, ścieżki ze spacjami, BOM/CRLF konfiguracji, wyłączenie konwersji ścieżek MSYS, wybranie dystrybucji i zachowanie kodu błędu. Konfiguracja jest odczytywana jako dane, a nie wykonywana.

Obie grupy testów przeszły. Testy zapisują odizolowane projekty w `scratch/workflow-test-*` i `scratch/windows-test-*`. Pliki `.out` pochodzące z atrapy są oznaczone jako **MOCK — NOT A FLUKA SIMULATION**. Nie są wynikami fizycznymi.

## Granice sprawdzenia

- Atrapa WSL sprawdza argumenty dispatchera Bash; nie potwierdza jeszcze działania rzeczywistego procesu Windows → WSL → Linux. Weryfikacja tego połączenia czeka na instalację WSL.
- Git Bash w testowanym trybie emulował dowiązania symboliczne kopiowaniem pliku. Test rzeczywistego dowiązania wymaga późniejszego uruchomienia pod Linuksem.
- W sandboxie Codexa Git Bash otrzymywał odmowę dostępu przy tworzeniu katalogów. Testy i przygotowanie przebiegu wykonano za zgodą poza sandboxem, wyłącznie w folderze projektu.
- Nadal potrzebne są: przegląd geometrii i komunikatów scoringu we Flair, wyjaśnienie ostrzeżenia BLCCRE, określenie docelowego celu i parametrów modelu oraz walidacja fizyczna. 10 000 historii w jednym cyklu jest większą próbką techniczną, ale nie daje oceny niepewności między cyklami ani nie potwierdza poprawności modelu.

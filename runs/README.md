# Przebiegi

Tworzy je `.\fluka.cmd prepare <nazwa>` w Windows lub `bash scripts/prepare-run.sh <nazwa>` w Linux. Każdy otrzymuje unikalny identyfikator z czasem UTC. `.\fluka.cmd status` pokazuje dostępne przebiegi.

- `input/`: zachowana kopia definicji przypadku.
- `work/`: pliki wejściowe i surowe wyniki FLUKA, w tym seedy kolejnych cykli.
- `manifest.json`, `inputs.sha256`: pochodzenie oraz kompletna lista sum kontrolnych obu kopii wejść (schemat 2).
- `tooling/`, `tooling.sha256`: archiwum skryptu przygotowania; przy starcie także faktycznie użyty runner, którego hash trafia do `execution.txt`.
- `note.txt`: miejsce na notatkę do przebiegu, edytowalne bez zmiany wejść modelu.
- `status.txt`: stan techniczny przygotowania/wykonania.
- `execution.txt`, `console.log`: parametry uruchomienia i log konsoli, powstają przy starcie.
- `.run-lock/`: znacznik rozpoczęcia, pozostaje także po zakończeniu.

Nie modyfikuj istniejących przebiegów; zmień przypadek i przygotuj następny. Kod wyjścia i obecność `.out` nie potwierdzają poprawności fizycznej. `running` może pozostać po awarii systemu — wtedy sprawdź procesy i pliki.

Wyniki są pomijane przez `.gitignore`. Kopia zapasowa musi obejmować cały katalog przebiegu, w tym pliki seed i metadane. Żaden skrypt projektu automatycznie ich nie usuwa.

# Elektrony 500 MeV na ołowianą ścianę — obliczenie techniczne

To osobny wariant modelu, bez zmian w `electron_500mev`. Oblicza widmo fluencji fotonów oraz dawkę pochłoniętą w powietrzu za roboczą osłoną. Nie jest to zatwierdzony projekt osłony ani wynik do oceny bezpieczeństwa radiologicznego.

## Przyjęte dane

| Parametr | Wartość |
| --- | --- |
| Cząstka i energia | Elektron, 500 MeV energii kinetycznej |
| Ładunek paczki | 20 pC, czyli około `1.2483 × 10^8` elektronów |
| Profil poprzeczny | Gaussowski, `sigma_x = sigma_y = 1 mm`, wycentrowany i padający prostopadle |
| Karta BEAM | Ujemne szerokości oznaczają FWHM; `2.35482 mm = 0.235482 cm` dla obu osi |
| Profil czasowy | Gaussowski, FWHM = 100 ns; transport FLUKA liczy wynik zintegrowany po paczce, bez rozkładu czasowego |
| Ściana | Blok predefiniowanego ołowiu, `10 × 10 × 10 cm`, środek osi wiązki |
| Otoczenie | Powietrze w modelowanej przestrzeni |
| Miejsce pomiaru | Warstwa powietrza `10 × 10 × 1 cm`, środek 20 cm za tylną powierzchnią Pb |
| Statystyka | 100 000 historii w jednym przebiegu technicznym |
| Widmo fotonów | USRTRACK, 100 przedziałów logarytmicznych od 1 keV do 500 MeV, uśrednione po warstwie powietrza |
| Dawka | USRBIN `DOSE-EM` i `DOSE` w powietrzu, w siatce `31 × 31 × 1` |

Liczbę elektronów wyznaczono z `N = |Q|/e`. Wynik dawki FLUKA w GeV/g na primary należy przemnożyć przez `1.602176462 × 10^-7 Gy/(GeV/g)` oraz przez liczbę elektronów w paczce. `DOSE-EM` oznacza dawkę z depozycji elektromagnetycznej (elektrony, pozytony i fotony); `DOSE` obejmuje wszystkie transportowane składniki. Są to dawki pochłonięte w powietrzu, nie dawka równoważna w Sv.

FWHM paczki czasowej nie zmienia zintegrowanego wyniku transportu. Nie wyznaczamy dawki szczytowej ani dawki na sekundę, ponieważ standardowe karty źródła użyte w tym przypadku nie symulują rozkładu czasowego paczki i opóźnień wtórnych.

Wynik widma jest fluencją fotonów w warstwie pomiarowej, a nie bezpośrednio „widmem lampy rentgenowskiej”; fotony z wysokoenergetycznego hamowania mogą mieć energię gamma. Pojedynczy przebieg nie zapewnia niezależnego oszacowania błędu między cyklami. Raport startowy FLUKA zawiera ostrzeżenia BLCCRE dla AIR (maksymalny błąd dopasowania 1,1%) i LEAD (54,5% przy `beta2 = 0.37014`). Pojawiają się podczas przygotowania parametrów materiałowych dla transportu; nie oznaczają przerwania obliczeń, ale ich wpływ wymaga przeglądu. Nie wyłączać modelu rozpraszania w celu ukrycia ostrzeżenia. Nie używać wyniku do doboru rzeczywistej osłony ani zgodności z limitami bez walidacji i przeglądu specjalisty ochrony radiologicznej.

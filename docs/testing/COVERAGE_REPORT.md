# Coverage-Bericht

Messdatum: 23. Oktober 2026

| Kennzahl | Ergebnis | Nachweis |
|---|---:|---|
| Gesammelte Tests | 361 | vollständiger pytest-Lauf |
| Bestandene/fehlgeschlagene/übersprungene Tests | 361 / 0 / 0 | vollständiger pytest-Lauf |
| Produktivzeilen | 4.498 | erzeugte `coverage.xml` |
| Abgedeckte Produktivzeilen | 2.860 | erzeugte `coverage.xml` |
| Line Coverage | 63,58 % | 2.860 / 4.498 |
| Branch Coverage | 51,18 % | 649 / 1.268 |
| Kombinierte pytest-cov Coverage | 60,86 % | vollständiger pytest-Lauf |
| Erzwungene Mindestquote | 60 % | `pytest.ini` |

Die Messung ist reproduzierbar und umfasst Line- und Branch-Coverage. Das vom
Auftrag geforderte Ziel von mindestens 80 % ist noch nicht erreicht. Besonders
die administrativen Sync-, Token-, Missing-Parts- und Importpfade benötigen
weitere fachliche Vertrags- und Fehlertests. Die zuvor bei 16 % liegende
Schwelle wurde auf die durch Volltestläufe belegten 60 % angehoben.

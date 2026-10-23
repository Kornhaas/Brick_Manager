# Coverage-Bericht

Messdatum: 23. Oktober 2026

| Kennzahl | Ergebnis | Nachweis |
|---|---:|---|
| Gesammelte Tests | 355 | vollständiger pytest-Lauf |
| Bestandene/fehlgeschlagene/übersprungene Tests | 355 / 0 / 0 | vollständiger pytest-Lauf |
| Produktivzeilen | 4.419 | erzeugte `coverage.xml` |
| Abgedeckte Produktivzeilen | 2.781 | erzeugte `coverage.xml` |
| Line Coverage | 62,93 % | 2.781 / 4.419 |
| Branch Coverage | 50,56 % | 631 / 1.248 |
| Kombinierte pytest-cov Coverage | 60,21 % | vollständiger pytest-Lauf |
| Erzwungene Mindestquote | 60 % | `pytest.ini` |

Die Messung ist reproduzierbar und umfasst Line- und Branch-Coverage. Das vom
Auftrag geforderte Ziel von mindestens 80 % ist noch nicht erreicht. Besonders
die administrativen Sync-, Token-, Missing-Parts- und Importpfade benötigen
weitere fachliche Vertrags- und Fehlertests. Die zuvor bei 16 % liegende
Schwelle wurde auf die durch Volltestläufe belegten 60 % angehoben.

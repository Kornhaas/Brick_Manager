# Anwendungsfunktionen

Diese Übersicht beschreibt die dauerhaft vorhandenen Bereiche der Webanwendung. Detailverhalten wird durch die jeweiligen Routen, Templates und Tests definiert; historische Funktionsnotizen befinden sich unter `docs/history/features/`.

| Bereich | Einstieg | Zweck |
| --- | --- | --- |
| Start und Gesundheit | `/`, `/health` | Übersicht und Betriebsstatus |
| Set-Suche und -Pflege | `/set_search`, `/set_maintain` | Katalogsets hinzufügen, physische Kopien und Mengen verwalten |
| Fehlteile | `/missing_parts` | Fehlende reguläre, Ersatz- und Minifigurenteile ermitteln und Mengen erfassen |
| Teile und Lagerorte | `/lookup_part`, `/part_location`, `/box_maintenance` | Teile finden, Lagerplätze pflegen und Boxen verwalten |
| Etiketten | Set- und Boxpflege | Label-PDFs erzeugen und Druckstatus führen |
| Datenimport und Synchronisierung | `/import_data`, `/admin/sync` | Rebrickable-Katalog importieren und bewusst angestoßene Abgleiche ausführen |
| Konfiguration | `/token_management` | API-Tokens verwalten |
| Bauanleitungen | `/building_instructions` | Lokale Anleitungsdateien bereitstellen |

## Desktop-API

Der Desktop-Client verwendet die versionierte API unter `/api/v1`. Sie stellt Teile, Setzuordnungen und Lagerorte bereit und erlaubt das Aktualisieren eigener Mengen und Lagerorte. Jeder Request verlangt einen konfigurierten Bearer-Key. Vertragsdetails und Sicherheitsvorgaben stehen in der [Referenzarchitektur](../architecture/reference-architecture.md) und in der [Konfiguration](../reference/configuration.md).

## Bedienungsgrundsätze

- Mehrere `user_sets` mit derselben Setnummer sind zulässig und repräsentieren physische Kopien.
- Ersatzteile bleiben bei Mengen- und Fehlteilberechnungen von regulären Teilen getrennt.
- Ein Teil kann mehrere Lagerorte haben; Änderungen müssen den betroffenen Ort eindeutig adressieren.
- Externe Abgleiche und Katalogimporte können Daten verändern. Sie werden bewusst angestoßen und ersetzen keine Sicherungsstrategie.

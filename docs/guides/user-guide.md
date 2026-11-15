# Anwendungsfunktionen

Diese Übersicht beschreibt die dauerhaft vorhandenen Bereiche der Webanwendung. Detailverhalten wird durch die jeweiligen Routen, Templates und Tests definiert; historische Funktionsnotizen befinden sich unter `docs/history/features/`.

| Bereich | Einstieg | Zweck |
| --- | --- | --- |
| Start und Gesundheit | `/`, `/health` | Übersicht und Betriebsstatus |
| Set-Suche und -Pflege | `/set_search`, `/set_maintain` | Katalogsets hinzufügen, physische Kopien und Mengen verwalten |
| Fehlteile | `/missing_parts` | Fehlende reguläre, Ersatz- und Minifigurenteile ermitteln und Mengen erfassen |
| Physisches Lager | `/warehouse` | Behälter, Stapel, Mengen, bestätigte Bewegungen und manuelle Archivprüfung; [Anleitung](warehouse.md) |
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

## Mengen speichern und Setlisten verwenden

In der Setpflege zeigt eine Mengenänderung „Wird gespeichert …“, „Gespeichert.“
oder einen bleibenden Fehlerhinweis. Bei Fehlern bleiben Eingaben erhalten und
„Erneut speichern“ versucht die Speicherung erneut. Ganze Mengen von null bis
zur benötigten Anzahl sind zulässig; Dezimalwerte werden nicht still gerundet.
Schnelle Folgeeingaben werden pro Teilezeile nacheinander gespeichert. Enter/Tab
bleiben nutzbar. „Save Changes“ wartet auf laufende Mengenänderungen; nach Wechsel
zu einem anderen Set wird kein verspäteter Formularabschluss ausgeführt.

Die Dashboard-Detailansichten verwenden ebenfalls eine Speicherwarteschlange,
zeigen Fehler mit „Retry save“ und übernehmen die tatsächlich vom Server
bestätigte Menge. Reguläre Teile und Minifigurenteile werden eindeutig
unterschieden, auch bei gleicher interner Nummer. Bei einer mehrdeutigen Anfrage
eines alten Clients wird keine Menge verändert.

Die Setliste berechnet ihre angezeigten Summen ohne vollständige Teilelisten zu
laden. Ein leerer Themenfilter bleibt leer und beeinflusst nachfolgende Suchen
oder Seitenwechsel nicht unbemerkt. Die weiterhin vorhandenen Bulk-Schaltflächen
zum vollständigen Befüllen/Zurücksetzen verändern zunächst Formularwerte; sie
werden erst mit „Save Changes“ übernommen.

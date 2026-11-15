# KI-Zusammenarbeit

Brick Manager enthält versionierte Anweisungen für KI-gestützte Entwicklung. `AGENTS.md` ist der Einstieg, `.codex/skills/` enthält fachliche Arbeitsabläufe und `.codex/agents/` die sieben spezialisierten Agenten. Die vorhandenen Entwicklungs-, Daten-, Integrations- und Test-Skills werden weiterverwendet.

## Rollen verwenden

| Rolle | Beispielauftrag |
| --- | --- |
| `architect` | „Prüfe die Modulgrenzen des Lagerort-Workflows und schlage eine überschaubare Verbesserung vor.“ |
| `senior_developer` | „Implementiere die vereinbarte Änderung einschließlich aller UI- und Route-Verbraucher.“ |
| `tester` | „Reproduziere den Mengenfehler mit einem Regressionstest und prüfe die Korrektur.“ |
| `usability_expert` | „Prüfe die vorhandene Lagerort-Zuweisung auf Tastatur- und Touch-Bedienbarkeit.“ |
| `security_expert` | „Prüfe die Upload-Route anhand des Quellcodes auf erreichbare Sicherheitsprobleme.“ |
| `database_architect` | „Plane die Migration eines neuen Sammlungsfeldes einschließlich Datenerhalt und Wiederholbarkeit.“ |
| `ux_designer` | „Entwirf einen verständlichen Lagerort-Dialog mit Leer-, Lade-, Fehler- und Erfolgszustand.“ |

Beispiel für einen größeren Auftrag:

> Lass architect den betroffenen Ablauf untersuchen, usability_expert die Bedienung bewerten und security_expert die Eingabegrenzen prüfen. Lass anschließend senior_developer die vereinbarte Änderung und tester die Regressionstests umsetzen. Ziehe database_architect hinzu, falls bestehende Daten verändert werden.

Der koordinierende Agent verteilt begrenzte Aufgaben und konkrete Dateizuständigkeiten. Unabhängige Reviews können parallel laufen; Änderungen an derselben Datei und voneinander abhängige Arbeiten erfolgen nacheinander. Er integriert die Ergebnisse und führt die abschließenden Prüfungen durch. Ein kleiner Auftrag benötigt nur die passenden Rollen. Usability bewertet den vorhandenen Ablauf; UX-Design beschreibt die angestrebte Interaktion.

Skills lassen sich auch direkt anfordern, beispielsweise: „Nutze $brick-manager-ux für ein Review der Teile-Suche.“ Rollen laden ihren primären Skill und bei Bedarf zusätzliche Fach-Skills.

## Einrichtung und Grenzen

Die Agenten sind als projektbezogene TOML-Dateien mit `name`, `description` und `developer_instructions` angelegt, entsprechend der [offiziellen Codex-Dokumentation](https://learn.chatgpt.com/docs/agent-configuration/subagents). Es werden keine Modelle, Zugangsdaten, globalen Einstellungen oder zusätzlichen Dienste vorausgesetzt. Modell und Berechtigungen kommen aus der jeweiligen Sitzung.

Starte nach dem Aktualisieren der Dateien eine neue Codex-Sitzung im Repository und prüfe, ob der verwendete Client die Projektagenten und Skills anbietet. Verfügbarkeit und parallele Ausführung hängen vom Client und den Sitzungsvorgaben ab. Falls eigene Agententypen nicht unterstützt werden, kann der Hauptagent die jeweilige TOML-Datei lesen und die Rolle selbst übernehmen; das ist kein unabhängiger Review. Die Dateien allein starten keine Hintergrundagenten.

Die Sammlung bleibt geschützt: keine echten Datenbanken für Experimente, keine Zugangsdaten in Ausgaben, keine Live-Schreibzugriffe auf externe Dienste, Resets, Restores oder Deployments ohne ausdrücklichen Auftrag. Review-Aufträge erlauben nicht automatisch Produktänderungen.

## Prüfung dieser Einrichtung

Bei Änderungen an Skills den Validator aus dem installierten `skill-creator` auf die betroffenen Skill-Verzeichnisse anwenden. Agentendateien mit `tomllib` auf gültiges TOML und die drei erforderlichen Felder prüfen; außerdem die referenzierten Skills und Dokumentationslinks kontrollieren.

Ein funktionaler Probelauf in einem unterstützten Client kann lauten: „Lass architect und tester jeweils ohne Dateiänderungen den Lagerort-Workflow untersuchen und ihre Ergebnisse getrennt liefern.“ Erst ein solcher Lauf bestätigt, dass dieser Client die Rollen tatsächlich startet. Eine Syntaxprüfung bestätigt ausschließlich die Konfigurationsdateien.

# Modell-Kurzreferenz

Die verbindlichen SQLAlchemy-Deklarationen stehen in `brick_manager/models.py`. Das vollständige Tabelleninventar, Beziehungen, Statuswerte und Migrationsregeln beschreibt das [Datenbankschema](database-schema.md).

| Gruppe | Modelle |
| --- | --- |
| Sammlung | `User_Set`, `User_Parts`, `User_Minifigures`, `UserMinifigurePart`, `PartStorage`, `CollectionSnapshot` |
| Rebrickable-Katalog | Kategorien, Farben, Teile, Beziehungen, Elemente, Themes, Sets, Minifiguren und Inventartabellen |
| Konfiguration | `ConfigSettings` mit optional verschlüsselten Werten |

Bei einer Modelländerung: Modell und Verhaltenstest aktualisieren, für bestehende Datenbanken eine vorwärtsgerichtete Migration ergänzen, das Schema anpassen und sicherstellen, dass Katalogimporte keinen sammlungseigenen Zustand verlieren.

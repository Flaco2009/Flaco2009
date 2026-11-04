<a href="https://flaco2009.github.io/Flaco2009/"><img src="https://raw.githubusercontent.com/Flaco2009/Flaco2009/output/banner.svg" alt="Live-Banner: Feuerwachturm über den Baumspitzen, folgt Jahreszeit, Wetter und Uhrzeit in Zürich" width="100%"></a>

<p align="center">
  <a href="https://flaco2009.github.io/Flaco2009/?open=weather"><img src="assets/buttons/wetter.svg" alt="Wetter wählen" height="40"></a>&nbsp;
  <a href="https://flaco2009.github.io/Flaco2009/?open=season"><img src="assets/buttons/jahreszeit.svg" alt="Jahreszeit wählen" height="40"></a>&nbsp;
  <a href="https://flaco2009.github.io/Flaco2009/?open=time"><img src="assets/buttons/uhrzeit.svg" alt="Uhrzeit wählen" height="40"></a>
</p>

<details>
<summary><b>Über diesen Banner</b></summary>
<br>

Ein Feuerwachturm über einem Meer aus Baumspitzen. Der Banner baut sich alle 30 Minuten neu und folgt dabei der echten Welt:

| | |
|---|---|
| **Uhrzeit** | Sonne und Mond nach dem echten Sonnenstand in Zürich, Dämmerung, Sterne, Sternschnuppen |
| **Jahreszeit** | Frühling blüht, Sommer mit Glühwürmchen, Herbst färbt die Lärchen, Winter verschneit |
| **Wetter** | zufällig, wechselt alle 3 Stunden: klar, wolkig, Regen, Gewitter, Nebel, Schnee |
| **Dezember** | Lichterketten am Turm, Mini-Baum auf dem Umlauf, Stern auf der Antenne |

<table>
<tr>
<td><img src="assets/previews/fruehling.webp" alt="Frühlingsmorgen"><br><sub>Frühlingsmorgen</sub></td>
<td><img src="assets/previews/sommer-nacht.webp" alt="Sommernacht mit Glühwürmchen"><br><sub>Sommernacht</sub></td>
</tr>
<tr>
<td><img src="assets/previews/gewitter.webp" alt="Sommergewitter"><br><sub>Gewitter</sub></td>
<td><img src="assets/previews/herbst-nebel.webp" alt="Herbstnebel"><br><sub>Herbstnebel</sub></td>
</tr>
<tr>
<td><img src="assets/previews/winter-schnee.webp" alt="Schneefall im Winter"><br><sub>Schneefall</sub></td>
<td><img src="assets/previews/dezember-nacht.webp" alt="Dezembernacht mit Lichterketten"><br><sub>Dezembernacht</sub></td>
</tr>
</table>

Alles wird von [`generate.py`](generate.py) als animiertes SVG gezeichnet, ohne Bilder oder Libraries. Eine [GitHub Action](.github/workflows/banner.yml) rendert es alle 30 Minuten neu.

</details>

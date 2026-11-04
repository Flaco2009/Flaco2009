<a href="https://flaco2009.github.io/Flaco2009/?user=Flaco2009"><img src="https://raw.githubusercontent.com/Flaco2009/Flaco2009/output/banner.svg" alt="Live banner: a fire lookout above the treetops that follows the real season, weather and time of day" width="100%"></a>

<p align="center">
  <a href="https://flaco2009.github.io/Flaco2009/?user=Flaco2009&open=weather"><img src="assets/buttons/weather.svg" alt="Pick the weather" height="40"></a>&nbsp;
  <a href="https://flaco2009.github.io/Flaco2009/?user=Flaco2009&open=season"><img src="assets/buttons/season.svg" alt="Pick the season" height="40"></a>&nbsp;
  <a href="https://flaco2009.github.io/Flaco2009/?user=Flaco2009&open=time"><img src="assets/buttons/time.svg" alt="Pick the time" height="40"></a>
</p>

<details>
<summary><b>About this banner</b></summary>
<br>

A fire lookout above a sea of treetops. The banner redraws itself every 30 minutes and follows the real world:

| | |
|---|---|
| **Time** | sun and moon follow the real sun position at your place, dusk, stars, shooting stars |
| **Season** | spring blossoms, summer fireflies, autumn larches turn gold, winter snow |
| **Weather** | random, changes every 3 hours: clear, cloudy, rain, thunderstorm, fog, snow |
| **December** | string lights on the tower, a tiny tree on the catwalk, a star on the antenna |

<table>
<tr>
<td><img src="assets/previews/spring-morning.webp" alt="Spring morning"><br><sub>Spring morning</sub></td>
<td><img src="assets/previews/summer-night.webp" alt="Summer night with fireflies"><br><sub>Summer night</sub></td>
</tr>
<tr>
<td><img src="assets/previews/thunderstorm.webp" alt="Summer thunderstorm"><br><sub>Thunderstorm</sub></td>
<td><img src="assets/previews/autumn-fog.webp" alt="Autumn fog"><br><sub>Autumn fog</sub></td>
</tr>
<tr>
<td><img src="assets/previews/winter-snow.webp" alt="Winter snowfall"><br><sub>Snowfall</sub></td>
<td><img src="assets/previews/december-night.webp" alt="December night with string lights"><br><sub>December night</sub></td>
</tr>
</table>

### Customize it

The buttons above open the playground. Pick weather, season, time, name and place, choose how long it should last and hit **Save**. GitHub opens with a prefilled issue, you click **Create**, and about a minute later your profile banner is updated. **Reset to auto** brings everything back to automatic. Only the owner of the repo can change it.

### Get your own

1. [Create a repo from this template](https://github.com/new?template_name=Flaco2009&template_owner=Flaco2009), name it **exactly like your GitHub username** and make it **public**
2. Done. Within 30 minutes the banner shows up on your profile with your name
3. Open the [playground](https://flaco2009.github.io/Flaco2009/), enter your username, set your place and save

Everything is drawn by [`generate.py`](generate.py) as an animated SVG, no images or libraries. A [GitHub Action](.github/workflows/banner.yml) re-renders it every 30 minutes, settings live in [`config.json`](config.json).

</details>

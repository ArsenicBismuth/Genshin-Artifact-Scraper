# Genshin Artifact Scraper
Automatically scrape all of your artifacts in Genshin Impact. Features:

- Simple recalibration (2 steps).
- GUI to select OCR regions.
- Regions reinitialization (7 steps).
- Macro to iterate through artifacts.
- File handling (using pickle).
- Manual mode (no macro).

While I've made the program to be very user-friendly and versatile, ultimately the scope is too big for something that's originally started as a personal project.

Please play around with the parameters and calibration to get the best result. I've made sure to properly comment and tidy up the programs as best as I could so that you can easily modify it.

Originally forked from [Genshin Artifact Rater](https://github.com/shrubin/Genshin-Artifact-Rater) by [shrubin](https://github.com/shrubin/Genshin-Artifact-Rater/commits?author=shrubin "View all commits by shrubin"). My program uses their parsing and rating subroutines.

Some features I feel as necessary in the future:
- .json export.
- Full process example video.
- Visual guide during region selection.

### Setup
```
python -m pip install -r requirements.txt
conda install -c conda-forge tesserocr
```

### Usage
As Genshin Impact runs on Admin, you need to run this with admin privileges. Otherwise, input events (mouse click) won't be recognized. But, you can try the manual mode (no admin required) by replacing `main.py` in this guide to `manual.py` (any item containing `*` symbol doesn't exist on manual mode).

Make sure to run this while in the inventory menu, not in the character selection menu.

Try to run once to calibrate:
```
python main.py -o
```
Recalibrate the coordinates by selecting regions in these order:

1. Colored box area of the artifact.
2. First 2x2 artifact tiles*.

About the selection GUI:

- You can preview your selection right away.
- Keep selecting region to continue zooming in.
- Right click to zoom out a bit, then reselect again.
- Close the window to finalize your selection.

Once you're done, you'll be given this output if successful:

```
+20 Plume
 - ATK 311
 - ATK% 5.8
 - CRIT DMG% 14.8
 - DEF 39
 - Energy Recharge% 16.2
Gladiator's Finale
Total: 8.14 (65.15%)
  Main: 4.00 (100.00%)
  Sub: 4.14 (48.75%)
```

If recalibration isn't successful, initialize the regions by selecting in these order (these instruction can be seen on the window title):

1. Artifact type.
2. Mainstat type.
3. Mainstat value.
4. Artifact level.
5. All substats & set name.
6. Artifact colored area.
7. First 2x2 artifact tiles*.

Then start scraping:
```
python main.py
```
### Parameters
You may play around with these simple parameters in the `main.py` file.
```
# Configs
LANG = tr.en()  # Language setting, placeholder
DIR = "./data/" # Output directory

MENU = [7,5,2]  # Menu dimension, x,y,page
SCROLL = 10*MENU[1]-1  # Scroll multiplier for page switch
```
To run debugging mode, use `-d` argument:
```
python main.py -d       # Full run + debug
python main.py -o -d    # Single run + debug
```
Also, you may change the stat weight in the `rate.py` file.
```
weights = {lang.hp: 0, lang.atk: 0.5, f'{lang.atk}%': 1, f'{lang.er}%': 0.5, lang.em: 0.5,
               f'{lang.phys}%': 1, f'{lang.cr}%': 1, f'{lang.cd}%': 1, f'{lang.elem}%': 1,
               f'{lang.hp}%': 0, f'{lang.df}%': 0, lang.df: 0, f'{lang.heal}%': 0}
```
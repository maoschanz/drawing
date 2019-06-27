# Drawing

## A simple drawing application for Linux.

This application is a basic image editor, similar to Microsoft Paint, but aiming at the GNOME desktop.

PNG, JPEG and BMP files are supported.

Besides GNOME, more traditional design layouts are available too, as well as an [elementaryOS layout](./data/screenshots/elementary.png). It should also be compatible with [Purism's Librem 5 phone](./data/screenshots/librem_preview.png).

### Available tools

(and a few of their options)

Drawing tools:

| Tool      | Options        |
|:---------:|:--------------:|
|Pencil     |Dashes, eraser, …|
|Rectangle  |Filling         |
|Circle     |Regular circle or oval; Filling
|Polygon    |Filling         |
|Free shape |Filling         |
|Line       |Arrow, dashes, …|
|Arc        |Arrow, dashes, …|
|Insert text|Font and font size|
|Selection  |Rectangle/free shape/adjacent color|
|Color picker|               |
|Paint      |Remove a color  |

<!--|Brush      |           |Not done yet-->

Canvas/selection edition tools:

| Tool      | Options   | Remarks |
|:---------:|:---------:|:-------:|
|Crop       |           |The previewed picture isn't at the actual scale
|Flip       |Horizontally or vertically
|Scale      |Keep proportions or not
|Rotate     |           |         |
|Saturate   |           |         |

<!-- |Matrix     |           |         |Not done yet -->

### Available languages

- Castillan (thanks to [Adolfo Jayme-Barrientos](https://github.com/fitojb) and [Xoan Sampaiño](https://github.com/xoan))
- Dutch (thanks to [Heimen Stoffels](https://github.com/Vistaus))
- English
- French
- German (thanks to [Onno Giesmann](https://github.com/Etamuk))
- Hebrew (thanks to [moriel5](https://github.com/moriel5) and [Shaked Ashkenazi](https://github.com/shaqash))
- Italian (thanks to [Jimmy Scionti](https://github.com/amivaleo))
- Russian (thanks to [Artem Polishchuk](https://github.com/tim77))
- Turkish (thanks to [Serdar Sağlam](https://github.com/TeknoMobil))

----

## Screenshots

### Default user interface (for GNOME/Budgie)

![GNOME/Budgie UI, here with the main menu opened](./data/screenshots/gnome_menu.png)

More screenshots:

- [Color chooser](./data/screenshots/gnome_colors.png)
- [Open/Import menu](./data/screenshots/gnome_open.png)
- [The selection tool and its menu](./data/screenshots/gnome_selection.png)
- [Drawing things on the picture with tools](./data/screenshots/gnome_tools.png)
- [Inserting text](./data/screenshots/gnome_text.png)
- [Adjusting the saturation](./data/screenshots/gnome_menu_saturation.png)

### Alternative user interfaces

- [elementaryOS UI](./data/screenshots/elementary.png)
- [MATE/Cinnamon UI](./data/screenshots/mate_selection.png)
- The default UI can be resized to be [compatible with the Purism Librem 5 phone](./data/screenshots/librem_preview.png)

----

## Installation

### Stable version

You can install it from flathub.org using the instructions on [this page](https://flathub.org/apps/details/com.github.maoschanz.drawing).

<!--Packages specific to distros: TODO-->

<!--- Fedora COPR-->
<!--- Solus-->
<!--- Arch & Manjaro AUR-->

### Unstable/nightly version

[See here](./INSTALL_FROM_SOURCE.md)


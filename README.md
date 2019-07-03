# Drawing

## A simple drawing application for Linux.

This application is a basic image editor, similar to Microsoft Paint, but aiming at the GNOME desktop.

PNG, JPEG and BMP files are supported.

Besides GNOME, some more traditional design layouts are available too, as well as an [elementaryOS layout](./data/screenshots/elementary.png). It should also be compatible with [Purism's Librem 5 phone](./data/screenshots/librem_options.png).

### Available tools

(and a few of their options)

Drawing tools:

| Tool      | Options        |
|:---------:|:--------------:|
|Pencil     |Dashes, eraser, …|
|Line       |Arrow, dashes, gradient …
|Arc        |Arrow, dashes, …|
|Insert text|Font and font size|
|Rectangle  |Filling         |
|Circle     |Regular circle or oval; Filling
|Polygon    |Filling         |
|Free shape |Filling         |
|Selection  |Rectangle/free shape/adjacent color
|Color picker|               |
|Paint      |Remove a color  |

<!--|Brush      |           |Not done yet-->

Canvas/selection edition tools:

| Tool      | Options   |
|:---------:|:---------:|
|Crop*      |           |
|Flip       |Horizontally or vertically
|Scale      |Keep proportions or not
|Rotate     |           |
|Saturate   |           |

<!-- |Matrix     |           |Not done yet -->

\*Remark: The previewed picture isn't at the actual scale.

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
- [Open/Import menu](./data/screenshots/gnome_open.png), with several tabs opened
- [The selection tool and its menu](./data/screenshots/gnome_selection.png)
- [Drawing things a blank picture with tools](./data/screenshots/gnome_tools_preview.png), with the preview opened
- [Inserting text](./data/screenshots/gnome_text.png)
- [Adjusting the saturation](./data/screenshots/gnome_menu_saturation.png), with the main menu opened

### Alternative user interfaces

- [elementaryOS UI](./data/screenshots/elementary.png)
- [MATE/Cinnamon UI](./data/screenshots/mate_scale.png)
- The default "GNOME" UI can be resized to be [compatible with the Purism Librem 5 phone](./data/screenshots/librem_options.png). [Youtube screencast](https://www.youtube.com/watch?v=xwfDnPd5NDU)

----

## Installation

### Stable version

>**Recommended**

You can install it from flathub.org using the instructions on [this page](https://flathub.org/apps/details/com.github.maoschanz.drawing).

### Native packages

>**Warning:** I don't maintain these packages, and thus I don't know what versions they provide.

- Fedora (29, 30 and Rawhide) ([COPR](https://copr.fedorainfracloud.org/coprs/atim/drawing/))
- Arch and Manjaro ([AUR](https://aur.archlinux.org/packages/drawing-git/))

<!-- TODO Solus -->
<!-- etc. -->

### Unstable/nightly version

[See here](./INSTALL_FROM_SOURCE.md)


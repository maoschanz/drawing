# Drawing

## A simple drawing application for Linux.

This application is a basic image editor, similar to Microsoft Paint, but aiming at the GNOME desktop.

PNG, JPEG and BMP files are supported.

Besides GNOME, some more traditional design layouts are available too, as well as an [elementaryOS layout](./docs/screenshots/elementary.png). It should also be compatible with [Purism's Librem 5 phone](./docs/screenshots/librem_options.png).

## Screenshots

### Default user interface (for GNOME/Budgie)

![GNOME/Budgie UI, here with the main menu opened](./docs/screenshots/gnome_menu.png)

More screenshots:

- [Color chooser](./docs/screenshots/gnome_colors.png)
- [Open/Import menu](./docs/screenshots/gnome_new.png), with several tabs opened
- [The selection tool and its menu](./docs/screenshots/gnome_selection.png)
- [Drawing things a blank picture with tools](./docs/screenshots/gnome_tools_preview.png), with the preview opened
- [Inserting text](./docs/screenshots/gnome_text.png)
- [Adjusting the saturation](./docs/screenshots/gnome_menu_saturation.png), with the main menu opened

### Alternative user interfaces

- [elementaryOS UI](./docs/screenshots/elementary.png)
- [Cinnamon UI](./docs/screenshots/cinnamon.png)
- [MATE UI](./docs/screenshots/mate_scale.png)
- The default "GNOME" UI can be resized to be compatible with the Purism Librem 5 phone. [Screenshot](./docs/screenshots/librem_options.png) and [screencast on Youtube](https://www.youtube.com/watch?v=xwfDnPd5NDU) (version 0.2).

----

## Installation

### Stable version

>**Recommended**

You can install it from flathub.org using the instructions on [this page](https://flathub.org/apps/details/com.github.maoschanz.drawing).

### Native packages

[![Packaging status](https://repology.org/badge/vertical-allrepos/drawing.svg)](https://repology.org/project/drawing/versions)

- Ubuntu 18.04 and 19.04: [PPA](https://launchpad.net/~cartes/+archive/ubuntu/drawing/)
- [Fedora (official repo)](https://apps.fedoraproject.org/packages/drawing) (29, 30 and Rawhide): `sudo dnf install drawing`
- Arch and Manjaro ([Arch "Community" repos](https://www.archlinux.org/packages/community/any/drawing/))

<!-- TODO Solus -->
<!-- etc. -->

### Unstable/nightly version

[See here](./INSTALL_FROM_SOURCE.md)

----

### Available languages

- Brazilian portugese (thanks to [Antonio Hauren](https://github.com/haurenburu))
- Castillan (thanks to [Adolfo Jayme-Barrientos](https://github.com/fitojb) and [Xoan Sampaiño](https://github.com/xoan))
- Dutch (thanks to [Heimen Stoffels](https://github.com/Vistaus))
- English
- French
- German (thanks to [Onno Giesmann](https://github.com/Etamuk))
- Hebrew (thanks to [moriel5](https://github.com/moriel5) and [Shaked Ashkenazi](https://github.com/shaqash))
- Italian (thanks to [Jimmy Scionti](https://github.com/amivaleo) and [Albano Battistella](https://github.com/albanobattistella))
- Russian (thanks to [Artem Polishchuk](https://github.com/tim77))
- Turkish (thanks to [Serdar Sağlam](https://github.com/TeknoMobil))

----

### Available tools

(last update: version 0.5-unstable)

#### Classic tools

- Pencil (options: dashes, blur, eraser, …)
- Line (options: arrow, dashes, blur, gradient, …)
- Arc (options: arrow, dashes, …)
- Insert text (options: font, shadow, font size, …)
- Rectangle (options: filling, …)
- Circle (options: oval, filling, …)
- Polygon (options: filling, …)
- Free shape (options: filling, …)
- Color picker
- Paint (options: remove a color, …)

#### Selection tools

These tools allow you to define an area (rectangle or free), which you can move, cut, copy, paste, edit with canvas tools, export, open as a new image, etc.

- Rectangle selection
- Free shape selection
- Adjacent color selection

#### Canvas/selection edition tools

These tools allow to edit the whole image, or to edit a selected part of it.

- Crop (remark: the previewed picture isn't at the actual scale)
- Scale (options: keep proportions or not)
- Rotate (rotate or flip)
- Blur
- Saturate (increase or decrease saturation)

----

[Donations (paypal)](https://paypal.me/maoschannz)


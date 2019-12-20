# Drawing (branch 0.4.x)

## A simple drawing application for Linux.

This application is a basic image editor, similar to Microsoft Paint, but aiming
at the GNOME desktop.

PNG, JPEG and BMP files are supported.

Besides GNOME, some more traditional design layouts are available too, as well
as an elementaryOS layout. It should also be compatible with smartphone screens
(Librem 5, PinePhone, etc.)

### Available tools

(and a few of their options)

Classic tools:

| Tool      | Options        |
|:---------:|:--------------:|
|Pencil     |Dashes, eraser, …|
|Line       |Arrow, dashes, gradient …
|Arc        |Arrow, dashes, …|
|Insert text|Font, shadow, font size|
|Rectangle  |Filling         |
|Circle     |Regular circle or oval; Filling
|Polygon    |Filling         |
|Free shape |Filling         |
|Color picker|               |
|Paint      |Remove a color  |

The selection tool allows you to define an area (rectangle or free), which you
can move, cut, copy, paste, edit with canvas tools, export, open as a new image,
etc.

Canvas/selection edition tools:

| Tool      | Options   |
|:---------:|:---------:|
|Crop*      |           |
|Flip       |Horizontally or vertically
|Scale      |Keep proportions or not
|Rotate     |           |
|Saturate   |           |

\*Remark: The previewed picture isn't at the actual scale.

### Available languages

- Brazilian portuguese (thanks to [Antonio Hauren](https://github.com/haurenburu))
- Castillan (thanks to [Adolfo Jayme-Barrientos](https://github.com/fitojb) and [Xoan Sampaiño](https://github.com/xoan))
- Danish (thanks to [scootergrisen](https://github.com/scootergrisen))
- Dutch (thanks to [Heimen Stoffels](https://github.com/Vistaus))
- English
- Finnish (thanks to [MahtiAnkka](https://github.com/mahtiankka))
- French
- German (thanks to [Onno Giesmann](https://github.com/Etamuk))
- Hebrew (thanks to [moriel5](https://github.com/moriel5) and [Shaked Ashkenazi](https://github.com/shaqash))
- Hungarian (thanks to [KAMI911](https://github.com/kami911))
- Italian (thanks to [Jimmy Scionti](https://github.com/amivaleo) and [Albano Battistella ](https://github.com/albanobattistella))
- Polish (thanks to [Piotr Komur](https://github.com/pkomur))
- Russian (thanks to [Artem Polishchuk](https://github.com/tim77))
- Turkish (thanks to [Serdar Sağlam](https://github.com/TeknoMobil))

----

## Screenshots

These screenshots show the main default user interface (for GNOME/Budgie), but
there are other more traditional window layouts (with a menubar and/or a toolbar
using diffent styles of icons).

![The primary menu opened](./help/C/figures/screenshot_menu.png)

![The options of the "arc" tool](./help/C/figures/screenshot_arc.png)

![Here part of the image is selected, and the selection menu is opened](./help/C/figures/screenshot_selection.png)

![An example of a tool modifying the whole canvas](./help/C/figures/screenshot_saturate.png)

The default "GNOME" UI can be resized to be compatible with the Purism Librem 5
phone. [Screenshot](./docs/screenshots/librem_options.png) and
[screencast on Youtube](https://www.youtube.com/watch?v=xwfDnPd5NDU) (version 0.2).

----

## Installation

### Stable version

>**Recommended**

You can install it from flathub.org using the instructions on [this page](https://flathub.org/apps/details/com.github.maoschanz.drawing).

### Native packages

[![Packaging status](https://repology.org/badge/vertical-allrepos/drawing.svg)](https://repology.org/project/drawing/versions)

- Ubuntu 18.04, 19.04 and 19.10: [PPA](https://launchpad.net/~cartes/+archive/ubuntu/drawing/)
- ["Snap" package](https://snapcraft.io/drawing)

### Unstable/nightly version

[See here](./INSTALL_FROM_SOURCE.md)


# Drawing

## A drawing application for the GNOME desktop.

This application is a simple image editor using Cairo for basic drawing operations, and following GNOME interface guidelines.

PNG, JPEG and BMP files are supported.

### Available tools

- Pencil
- Shape
    - Rectangle
    - Circle
    - Oval
- Polygon
- Line, arc, arrow, dashes
- Text
- Eraser
- Selection (rectangle or free shape)
    - Drag
    - Cut/copy
    - Paste/import from
    - Export to

The app can crop, scale or rotate the canvas or the selection.

#### Future tools ?

- Painting
- Brush
- Gradient

## Installation

Clone it, open it as a project with GNOME Builder, and run it (or export it as flatpak)

Or:

```
flatpak-builder --force-clean _build2/ --repo=_repo com.github.maoschanz.Drawing.json
flatpak --user remote-add --no-gpg-verify local-drawing-repo _repo
flatpak --user install local-drawing-repo com.github.maoschanz.Drawing
```

Or an other technique using meson directly (TODO)

## Screenshots

GNOME/Budgie UI (in French here):

![GNOME/Budgie UI](https://raw.githubusercontent.com/maoschanz/drawing/master/data/screenshots/screenshot_gnome_2.png)

MATE/Cinnamon UI:
![MATE/Cinnamon UI](https://raw.githubusercontent.com/maoschanz/drawing/master/data/screenshots/screenshot_mate_1.png)


Be sure to read [general contributing guidelines](../CONTRIBUTING.md#contribute-to-the-code)
first.

<!--[TOC]-->
<!--FIXME quand un objet retient qui l'a invoqué, c'est tjrs de la compo ??-->

# Overview

>See general-class-diagram.dia

## The application

`main.py` defines the application, which has:

- implementations of CLI handling methods
- some `GioAction`s
- a preferences window (`preferences.py`)
- a menubar (hidden with most layouts)
- an appmenu (for GNOME Shell ≤ 3.30)
- dialogs (about, shortcuts)
- several **windows**

## Windows

`window.py` defines a GtkApplicationWindow:

- some `GioAction`s
- a window's decorations can change quite a lot, which is mostly handled by
`deco_manager.py`. Three classes are defined in this file:
	- **`DrDecoManagerMenubar`** just hides or shows the menubar. Most of its
	methods are empty.
	- **`DrDecoManagerToolbar`** loads a toolbar from an UI file. This class
	extends `DrDecoManagerMenubar`, and will manage a small "hamburger menu" at
	the end of the toolbar if the menubar is hidden.
	- **`DrDecoManagerHeaderbar`** loads a headerbar from an UI file. This class
	extends `DrDecoManagerMenubar` but the menubar will always stay hidden.
	It handles how widgets are shown or hidden depending on the size of the
	window, and will display various menus depending on the visibility of the
	buttons, to ensure all features are always available.
- a window has several **tools**
- a window has several **images**
- `minimap.py` for the minimap, which shows a thumbnail of the currently opened image.
- each window has an **options_manager** (`options_manager.py`). It will display
the correct bottom bar (= the one required by the current **tool**) and manage
tools' options. All bottom options bars can be found in the sub-directories of
`src/optionsbars/`, and are specialized from `src/optionsbars/abstract_optionsbar.py`

## Images

`image.py` defines an image (= a tab), which contains:

- a `GdkPixbuf.Pixbuf` (as an attribute), named `main_pixbuf`, which corresponds
to the current state of the edited image.
- a file (`Gio.File`) which can be `None` (if it's a new image never saved).
- a history, managed by `history_manager.py`
- a selection, managed by `selection_manager.py`
- methods to manage the zoom and the scroll.
- methods to manage printing.
- methods to receive signals from the mouse, and transmit them to the tools.

# The tools

>See tools-class-diagram.dia

The tools are managed by a bunch of files in the `src/tools` directory.

>The relationship between the window and the tools is a
**[State](https://en.wikipedia.org/wiki/State_pattern)** design pattern.

The active tool's methods are called from the currently active image's code (or
the window's code) regardless of what tool is active. To achieve that, all tools
inherit from **abstract** classes defining common methods.

First of all, `src/tools/abstract_tool.py` defines how the tool will be added in
the UI, provides several wrappers to add options, to access the pixbufs, to add
an operation to the edition history, etc.

Other common features, when they don't depend on the image or the tool at all
(such as blurring, computing some paths, displaying an overlay on the image (for
the selection for example)), may be provided by one of the
`src/tools/utilities_*.py` files.

Then, an other layer of abstract classes is used, depending on the subcategory a
tool is in:

- the classic tools, draw on the main pixbuf using **`cairo`**
- the selection tools translates the user's input into operations using the
image's **selection_manager**. These operations are quite complex, and are
almost entirely managed in `abstract_select.py`.
- the "canvas tools" (scale/crop/rotate/filters/…) can be applied to the
selection pixbuf or the main pixbuf, and will use the image's `temp_pixbuf`
attribute to store a preview of their changes. These tools have to be
explicitely applied by the user, using a button in the bottom bar.

# The bottom bar

>See bottombar-class-diagram.dia

TODO

<!--TODO-->



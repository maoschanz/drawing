
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

## Tools

[See here](./design-tools.md)

## Bottom pane

[See here](./design-optionsbars.md)


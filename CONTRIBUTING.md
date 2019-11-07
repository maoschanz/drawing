# How to contribute to Drawing

----

## If you want to translate the app

#### I assume this will be the most usual contribution so i detail:

- Fork the repo and clone it on your disk.
- `git checkout 0.4` to contribute to the `0.4` branch.
- Add your language to `po/LINGUAS`.
- Build the app once, and then run `ninja -C _build drawing-update-po` at the root of the project. It will produce a `.po` file for your language.
- Use a text editor or [an adequate app](https://flathub.org/apps/details/org.gnome.Gtranslator) to translate the strings of this `.po` file. Do not translate the app id (`com.github.maoschanz.drawing`).
- If you want to test your translation:
	- GNOME Builder isn't able to run a translated version of the app so export it as a `.flatpak` file.
	- Install it with `flatpak install path/to/that/file`.
- Run `git add . && git commit && git push`
- Submit a "pull request"/"merge request".

----

## If you want to fix a bug or to add a new feature

- The issue has to be reported first.
- Tell on the issue that you'll try to fix it.

### Syntax

- Use tabs in `.py` files.
- Use 2 spaces in `.ui` or `.xml` files.
- Try to not do lines longer than 80 characters.
- In the python code, use double quotes for translatable strings and single quotes otherwise.
- Good comments explain *why* the code does it, if a comment needs to explain *what* it does, the code is probably bad.
- I like `GAction`s and i've added wrapper methods for using them, try to use that instead of directly connecting buttons/menu-items to a method.

Concerning design, try to respect GNOME Human Interface Guidelines as much as possible, while making your feature available from the (hidden by default) menubar.

### Explanation of the code

The `data` directory contains data useless to the execution (app icons, desktop launcher, settings schemas, appdata, …).
I know, it should contains the resources according to some people, but i don't care:
resources used by the app (`.ui` files, in-app icons, …) are in `src`, along with the python code.

- `main.py` defines the application, which has:
    - a preferences window (`preferences.py`)
    - a menubar (hidden with most layouts)
    - an appmenu (for GNOME Shell <= 3.30)
    - dialogs (about, shortcuts)
    - some `GioAction`s
    - implementations of CLI handling methods
    - several **windows**
- `window.py` defines a GtkApplicationWindow:
    - the **properties** dialog (`proporties.py`) depends on the window
    - a window's decorations can change quite a lot, which is partly handled by…
        - `headerbar.py` for the headerbar
        - `color_popover.py` for the color palettes (default bottom panel)
        - `minimap.py` for the minimap, which shows a thumbnail of the currently opened image
    - some `GioAction`s
    - a window has several **tools**
    - a window has several **images**
- `image.py` defines an image, which contains:
    - an "undo" history and a "redo" history
    - a selection, managed by `selection_manager.py`
    - a pixbuf (as an attribute), named `main_pixbuf`
- **tools** are managed by a bunch of files in the `tools` directory. There are several types of tools:
    - the selection translates users input into operations using the selection_manager
    - the "canvas tools" can be applied the selection pixbuf or the main pixbuf
    - the classic tools, draw on the main pixbuf using **`cairo`**

In my opinion, he complexity of the code comes mainly from 2 points:

- tools are window-wide, while operations, which are stored in the history, are image-wide
- the interactions with the selection are ridiculously complex and numerous _(defining, explicit applying, explicit canceling, import, clipboard methods, cancelled use by other tools, confirmed use by other tools, deletion, implicit applying, implicit canceling, …)_

<!-- UML diagrams: -->

<!-- ![UML diagrams](docs/uml.png) -->

>**If you find some bullshit in the code, or don't understand it, feel free to ask me about it.**

----

## If you find a bug

Usability and design issues are considered as bugs.

- If you can, try to check if it hasn't already been fixed but not released.
- Report it with:
	- OS version
	- Flatpak version
	- App version
	- If it's meaningful, screenshots.

----

## If you want a new feature

Usability and design issues are **not** considered as features.

- Report it as an issue, and explain what it does, not how it does it.
- Is it…
	- a general feature ?
	- a new standalone tool ?
	- a new option for an existing tool ?

----

#### And thank you for caring about this app!


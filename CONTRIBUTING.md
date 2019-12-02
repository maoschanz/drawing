How to contribute to Drawing

----

# If you want to translate the app

> I assume this will be the most usual contribution so i detail:

## If the translation doesn't exist at all

- Fork the repo and clone your fork on your disk.
- Add your language to `po/LINGUAS`.
- Build the app once, and then run `ninja -C _build drawing-update-po` at the root of the project. It will produce a `.po` file for your language in the `po` directory.
- Use a text editor or [an adequate app](https://flathub.org/apps/details/org.gnome.Gtranslator) to translate the strings of this `.po` file. Do not translate the app id (`com.github.maoschanz.drawing`).
- If you want to test your translation:
	- GNOME Builder isn't able to run a translated version of the app so export it as a `.flatpak` file.
	- Install it with `flatpak install path/to/that/file`.
- Run `git add . && git commit && git push`
- Submit a "pull request"/"merge request"

## If the translation exists but is incomplete

- Fork the repo and clone your fork on your disk.
- Find file corresponding to you language in the the `po` directory
- Use a text editor or [an adequate app](https://flathub.org/apps/details/org.gnome.Gtranslator) to translate the strings of this `.po` file. Do not translate the app id (`com.github.maoschanz.drawing`).
- If you want to test your translation:
	- GNOME Builder isn't able to run a translated version of the app so export it as a `.flatpak` file.
	- Install it with `flatpak install path/to/that/file`.
- Run `git add . && git commit && git push`
- Submit a "pull request"/"merge request"

----

# If you want to fix a bug or to add a new feature

- The issue has to be reported first
- Easy issues are tagged "**good first issue**"
- Tell on the issue that you'll try to fix it

>**If you find some bullshit in the code, or don't understand it, feel free to
ask me about it.**

## Syntax

- Use tabs in `.py` files.
- Use 2 spaces in `.ui` or `.xml` files.
- Try to not do lines longer than 80 characters.
- In the python code, use double quotes for translatable strings and single quotes otherwise.
- Good comments explain *why* the code does it, if a comment needs to explain *what* it does, the code is probably bad.
- I like `GAction`s and i've added wrapper methods for using them, try to use that instead of directly connecting buttons/menu-items to a method.

Concerning design, try to respect GNOME Human Interface Guidelines as much as
possible, while making your feature available from the (hidden by default)
menubar. If you're contributing to an alternative layout ("elementary OS",
"Cinnamon", …), just be sure to not hurt the UX with the GNOME layout (since it
is used on smartphone, it has to stay very resizable).

## Explanation of the code

The `data` directory contains data useless to the execution (app icons, desktop
launcher, settings schemas, appdata, …).

According to some people, it should contains the resources, but i don't care:
resources used by the app (`.ui` files, in-app icons, …) are in `src`, along
with the python code.

### The application itself

- `main.py` defines the application, which has:
    - a preferences window (`preferences.py`)
    - a menubar (hidden with most layouts)
    - an appmenu (for GNOME Shell ≤ 3.30)
    - dialogs (about, shortcuts)
    - some `GioAction`s
    - implementations of CLI handling methods
    - several **windows**
- `window.py` defines a GtkApplicationWindow:
    - the **properties** dialog (`properties.py`) depends on the window (despite showing image-wide infos)
    - a window's decorations can change quite a lot, which is partly handled by `headerbar.py` for the headerbar
    - some `GioAction`s
    - a window has several **tools**
    - a window has several **images**
    - `minimap.py` for the minimap, which shows a thumbnail of the currently opened image
    - each window has an **options_manager** (`options_manager.py`). It will display the correct bottom panel (`bottombar.py`) among the numerous bottom panels defined by **tools**, and manage tools' options. The most common bottom panel is using `color_popover.py` to provide a color selection menu.
- `image.py` defines an image, which contains:
    - an "undo" history and a "redo" history
    - a selection, managed by `selection_manager.py`
    - a pixbuf (as an attribute), named `main_pixbuf`

### The tools

The tools are managed by a bunch of files in the `src/tools` directory.

All tools inherit from **abstract** classes defining common methods. First of
all, `src/tools/abstract_tool.py` defines how the tool will be added in the UI,
provides several wrappers to add options, to access the pixbufs, to add an
operation to the edition history, etc. Other common features, when they don't
depend on the image or the tool at all (such as blurring, computing some paths,
displaying an overlay on the image (for the selection for example)), may be
provided by `src/tools/utilities_tools.py`.

Then, an other layer of abstract classes is used, depending on the subcategory a
tool is in:

- the classic tools, draw on the main pixbuf using **`cairo`**
- the selection tools translates the user's input into operations using the image's **selection_manager**
- the "canvas tools" can be applied the selection pixbuf or the main pixbuf (scale/crop/rotate/filters/…) and will use the image's `temp_pixbuf` attribute to store a preview of their changes. These tools have to be explicitely applied by the user.

In my opinion, the complexity of the code comes mainly from 2 points:

- tools are window-wide, while operations, which are stored in the history, are image-wide
- the interactions with the selection are ridiculously complex and numerous _(defining, explicit applying, explicit canceling, import, clipboard methods, use by other tools (cancelled or confirmed), deletion, implicit applying, implicit canceling, …)_

<!-- ### UML diagrams -->

<!-- ![UML diagrams](docs/uml.png) -->

----

# If you find a bug

Usability and design issues are considered as bugs.

- If you can, try to check if it hasn't already been fixed but not released.
- Report it with:
	- OS version
	- Flatpak version
	- App version
	- If it's meaningful, screenshots.

----

# If you want a new feature

Usability and design issues are **not** considered as features.

- Report it as an issue, and explain what it does, not how it does it.
- Is it…
	- a general feature?
	- a new standalone tool?
	- a new option for an existing tool?

----

>**And thank you for caring about this app!**


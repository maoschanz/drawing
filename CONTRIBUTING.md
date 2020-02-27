How to contribute to Drawing

- [If you find a bug](#bug-reports)
- [If you want a new feature](#feature-requests)
- [If you want to **translate** the app](#translating)
- If you want to fix a bug or to add a new feature:
	- [General guidelines](#contribute-to-the-code)
	- [Explanations about the code](#structure-of-the-code)
- [How to install from the source code](#install-from-source-code)
- [If you want to **package** the app](#packaging)

----

# Bug reports

Usability and design issues concerning existing features are bugs.

- If you can, try to **check if it hasn't already been fixed but not released**.
- Report it with informations required by the adequate issue template.
- If it's meaningful, try to include screenshots.

----

# Feature requests

Usability and design issues concerning existing features are **not** new features.

- If you can, try to **check if it hasn't already been added but not released**.
- Report it with informations required by the adequate issue template.
- In the report, explain **what** it does, **not how** it does it.

----

# Translating

- Fork the repo and clone your fork on your disk (see [installation instructions here](#with-gnome-builder-and-flatpak))
- **If the translation exists but is incomplete:**
	- Find the file corresponding to you language in the the `po` directory
- **If the translation doesn't exist at all:**
	- Add your language to `po/LINGUAS`
	- Build the app once, and then run `ninja -C _build drawing-update-po` at the root of the project. It will produce a `.po` file for your language in the `po` directory.
- Use a text editor or [an adequate app](https://flathub.org/apps/details/org.gnome.Gtranslator) to translate the strings of this `.po` file. Do not translate the app id (`com.github.maoschanz.drawing`).
- **(optional)** If you want to test your translation:
	- The flatpak SDK isn't able to run a translated version of the app, so export it as a `.flatpak` file and install it with `flatpak install path/to/that/file`.
	- Or (it's harder) [install it with `meson`](#with-git-and-meson).
- Run `git add . && git commit && git push`
- Submit a "pull request"/"merge request"

Notice that it will translate the unstable, unreleased version currently
developed on the `master` branch, while users may use versions with slightly
different labels you may not have translated. If you want to entirely translate
older versions, restart but run `git checkout 0.4` just after the step 1.

----

# Contribute to the code

### General guidelines

- It's better if an issue is reported first
- Easy issues are tagged "**good first issue**"
- Tell on the issue that you'll try to fix it

**If you find some bullshit in the code, or don't understand it, feel free to
ask me about it.**

To set up a development environment, see [here](#install-from-source-code).

### Syntax

- Use tabs in `.py` files.
- Use 2 spaces in `.ui` or `.xml` files.
- Try to not write lines longer than 80 characters.
- In the python code, use double quotes for strings the user might see, and
single quotes otherwise (paths, constants, enumerations, dict keys, …)
- Good comments explain *why* the code does what it does. If a comment explains
*what* it does, the comment is useless, or the code is bad.

I like `GAction`s and i've added wrapper methods for using them, try to use that
instead of directly connecting buttons/menu-items to a method.

### UI design

People sometimes like to design their apps in Glade, while here the main `.ui`
files are mere templates filled algorithmically according to the user's
settings, you kinda have to run the app to be sure of how your changes to it
actually look like.

Try to respect [GNOME Human Interface Guidelines](https://developer.gnome.org/hig/stable/)
as much as possible, while making your feature available from the menubar
(in `app-menus.ui`). The menubar is hidden in most cases, but it should contains
as many `GAction`s as possible for testing purposes (and also because searchable
menus still exist).

If you're contributing to an alternative layout ("elementary OS", "Cinnamon", or
any other), please be sure to not hurt the UX with the GNOME layout (since it's
the one used on smartphone, be careful it has to stay very resizable).

### Other remarks

In my opinion, the difficulties with the code can come mainly from 2 points:

- tools are window-wide, while the operations they produce, which are stored in
the history, are image-wide.
- the interactions with the selection are ridiculously complex and numerous
_(defining, explicit applying, explicit canceling, import, clipboard methods,
use by other tools (cancelled or confirmed), deletion, implicit applying,
implicit canceling, …)_ which can easily create small bugs.

----

# Structure of the code

The `data` directory contains data useless to the execution (app icons, desktop
launcher, settings schemas, appdata, …).

According to some people, it should contain the UI resources, but i don't care:
resources used by the app (`.ui` files, in-app icons, …) are in `src`, along
with the python code.

<!-- TODO ![UML diagrams](docs/uml.png) -->

### The application itself

`main.py` defines the application, which has:

- implementations of CLI handling methods
- some `GioAction`s
- a preferences window (`preferences.py`)
- a menubar (hidden with most layouts)
- an appmenu (for GNOME Shell ≤ 3.30)
- dialogs (about, shortcuts)
- several **windows**

`window.py` defines a GtkApplicationWindow:

- some `GioAction`s
- a "properties" dialog (`properties.py`). It depends on the window despite
showing image-wide infos.
- a window's decorations can change quite a lot, which is mostly handled by
`deco_manager.py`. Three classes are defined in this file:
	- `DrDecoManagerMenubar` just hides or shows the menubar. Most of its
	methods are empty.
	- `DrDecoManagerToolbar` loads a toolbar from an UI file. This class extends
	`DrDecoManagerMenubar`, and will manage a small "hamburger menu" at the end
	of the toolbar if the menubar is hidden.
	- `DrDecoManagerHeaderbar` loads a headerbar from an UI file. This class
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

`image.py` defines an image, which contains:

- an "undo" history and a "redo" history
- a selection, managed by `selection_manager.py`
- a `GdkPixbuf.Pixbuf` (as an attribute), named `main_pixbuf`, which corresponds
to the current state of the edited image.

### The tools

The tools are managed by a bunch of files in the `src/tools` directory.

>The relationship between the window and the tools is a
**[State](https://en.wikipedia.org/wiki/State_pattern)** design pattern.

The active tool's methods are called from the window's (or the current image's)
code regardless of what tool is active. To achieve that, all tools inherit from
**abstract** classes defining common methods.

First of all, `src/tools/abstract_tool.py` defines how the tool will be added in
the UI, provides several wrappers to add options, to access the pixbufs, to add
an operation to the edition history, etc. Other common features, when they don't
depend on the image or the tool at all (such as blurring, computing some paths,
displaying an overlay on the image (for the selection for example)), may be
provided by one of the `src/tools/utilities_*.py` files.

Then, an other layer of abstract classes is used, depending on the subcategory a
tool is in:

- the classic tools, draw on the main pixbuf using **`cairo`**
- the selection tools translates the user's input into operations using the
image's **selection_manager**. These operations are quite complex, and are
almost entirely managed in `abstract_select.py`.
- the "canvas tools" (scale/crop/rotate/filters/…) can be applied to the
selection pixbuf or the main pixbuf, and will use the image's `temp_pixbuf`
attribute to store a preview of their changes. These tools have to be
explicitely applied by the user.

----

# Install from source code

You will not get updates with this installation method so please do that only
for contributing to development, translations, testing, or packaging.

### With GNOME Builder and flatpak

This app is developed using _GNOME Builder_ and its support for `flatpak`:

- Open _GNOME Builder_
- Click on "Clone a repository…" and use this address: `https://github.com/maoschanz/drawing.git`
- Open it as a project with GNOME Builder
- Be sure the runtime is installed (if it doesn't suggest it automatically, <kbd>Ctrl</kbd>+<kbd>Return</kbd> → type `update-dependencies`)
- Click on the _Run_ button

### With `git` and `meson`

See [here](#dependencies) for the list of dependencies.

Get the code:

```
git clone https://github.com/maoschanz/drawing.git
```

Build the app:
```
cd drawing
meson _build
ninja -C _build
```

Install the app (system-wide):
```
sudo ninja -C _build install
```
(if you know the options to install user-wide, please tell)

The app can then be removed with:
```
cd _build
sudo ninja uninstall
```

### Others

<details><summary>With flatpak-builder (not recommended, that's just for me)</summary>
<p>

Initial setup of the local flatpak repository:
```
wget https://raw.githubusercontent.com/maoschanz/drawing/master/com.github.maoschanz.drawing.json
flatpak-builder --force-clean _build2/ --repo=_repo com.github.maoschanz.drawing.json
flatpak --user remote-add --no-gpg-verify local-drawing-repo _repo
flatpak --user install local-drawing-repo com.github.maoschanz.drawing
```

Update:
```
flatpak-builder --force-clean _build2/ --repo=_repo com.github.maoschanz.drawing.json
flatpak update
```

</p>
</details>

You can also build a debian package with the script `deb_package.sh`, but you
won't get updates that way, so don't do that. You probably don't have all the
dependencies to make it work anyway.

----

# Packaging

### Branches

The `master` branch is not stable and should not be packaged.

Stable versions for end-users are tagged, and listed on this Github repo's
"_Releases_" tab. For now, most of them are on the `0.4` branch.

### Dependencies

Dependencies to run the app:

- GObject Introspection (GI) for python3 (on Debian, it's `python3-gi`). A version ≥3.30.0 is required to run the code from the branch `master`. The branch `0.4` should be fine with any version.
- `cairo` library's GI for python3 (on Debian, it's `python3-gi-cairo`).
- GTK libraries' GI (on Debian, it's `gir1.2-gtk-3.0`).

Dependencies to build the app (Debian packages names):

- `meson`. The version required by the `meson.build` file at the root of the project can be changed if necessary, but please don't add this change to your commit(s).
- `appstream-util` (validation of the `.appdata.xml` file)
- `libglib2.0-dev-bin` (IIRC that one is to compress the `.ui` files and the icons into a `.gresource` file)

----





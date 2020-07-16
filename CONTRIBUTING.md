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

Use a text editor or [an adequate app](https://flathub.org/apps/details/org.gnome.Gtranslator)
to translate the strings of this `.po` file. There are comments in the file to
give context helping you to translate some strings, please take them into
account.

>Example of something translators can't guess so it's written in the comments:
since this app is a clone of MS Paint, `Paint;` (untranslated) has to be in the
list of keywords for finding the app in searchable menus or software centers.

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

**If you find anything weird in the code, or don't understand it, feel free to
ask me about it.**

To set up a development environment, see [here](#install-from-source-code).

### Syntax and comments

- Use 2 spaces in `.ui` or `.xml` files.
- Good comments explain *why* the code does what it does. If a comment explains
*what* it does, the comment is useless, or the code is bad.
- Upon translatable strings, comments explaining the context to translators are
welcome.

**In python code only:**

- Use actual tabs (4 columns wide).
- Try to not write lines longer than 80 characters.
- Use double quotes for strings the user might see, and single quotes otherwise
(paths, constants, enumerations, dict keys, …)

### UI design

People sometimes like to design their apps in Glade, but in Drawing, the main
`.ui` files are mere templates filled algorithmically according to the user's
settings, so you kinda have to run the app to be sure of how your changes to
these files actually look like.

Try to respect [GNOME Human Interface Guidelines](https://developer.gnome.org/hig/stable/)
as much as possible, while making your feature available from the menubar
(in `app-menus.ui`). The menubar is hidden in most cases, but it should contains
as many `GAction`s as possible for testing purposes (and also because searchable
menus still exist).

If you're contributing to an alternative layout ("elementary OS", "Cinnamon", or
any other), please be sure to not hurt the UX with the GNOME layout (since it's
the one used on smartphone, be careful it has to stay very resizable).

### Structure of the code

The `data` directory contains data useful for installation but useless to the
execution (app icons, desktop launcher, settings schemas, appdata, …).

According to some people, this directory should contain the UI resources, but
here no: resources used by the app (`.ui` files, in-app icons, …) are in `src`,
along with the python code.

<!-- TODO ![UML diagrams](docs/uml.png) -->

- See [here](./diagrams/README.md) for explanations about the code
- See [here](./diagrams/) for class diagrams (**WORK IN PROGRESS**)

### Other remarks

I like `GAction`s and i've added wrapper methods for using them, try to use that
instead of directly connecting buttons/menu-items to a method.

In my opinion, the difficulties with the code can come mainly from 3 points:

- tools are window-wide, while the operations they produce, which are stored in
the history, are image-wide.
- the interactions with the selection are ridiculously complex and numerous
_(defining, explicit applying, explicit canceling, import, clipboard methods,
use by the "canvas tools" (cancelled or confirmed), deletion, implicit applying,
implicit canceling, …)_ which can easily create small bugs.
- the horizontal and vertical scrollings (and their scrollbars) are managed
"manually" and quite poorly.

These 3 points sometimes lead to object-oriented spaghetti code.

If you change anything regarding the selection and/or the "canvas tools" (the
tools which can edit the selection content), make sure to test various scenarios
like this one:

1. several images edited in different tabs of the same window;
2. zoom and/or scroll;
3. select things, or import/paste things (in both tabs);
4. edit the selection (in both tabs, don't forget to click "apply" before
switching to the other tab);
5. unselect it (in both tabs);
6. undo/redo.

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

```sh
git clone https://github.com/maoschanz/drawing.git
```

Build the app:
```sh
cd drawing
meson _build
ninja -C _build
```

Install the app (system-wide):
```sh
sudo ninja -C _build install
```
(if you know the options to install user-wide, please tell)

The app can then be removed with:
```sh
cd _build
sudo ninja uninstall
```

### Others

<details><summary>With flatpak-builder (not recommended, that's just for me)</summary>
<p>

Initial setup of the local flatpak repository:
```sh
wget https://raw.githubusercontent.com/maoschanz/drawing/master/com.github.maoschanz.drawing.json
flatpak-builder --force-clean _build2/ --repo=_repo com.github.maoschanz.drawing.json
flatpak --user remote-add --no-gpg-verify local-drawing-repo _repo
flatpak --user install local-drawing-repo com.github.maoschanz.drawing
```

Update:
```sh
flatpak-builder --force-clean _build2/ --repo=_repo com.github.maoschanz.drawing.json
flatpak update
```

</p>
</details>

You can also build a debian package with the script `deb_package.sh`, but you
won't get updates that way, so don't do that. You probably don't have all the
dependencies to make the script work anyway.

----

# Packaging

### Branches

The `master` branch is not stable and **should not** be packaged.

<details><summary>(except if your distro have experimental repos)</summary>
<p>

<a href=https://wiki.debian.org/DebianExperimental>How to set up the debian
experimental repository</a>

```sh
sudo apt -t experimental install drawing
```

</p>
</details>

Stable versions for end-users are **tagged**, and listed in this Github repo's
"_Releases_" section. For now, most of them are on the `0.4` branch.

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







# Syntax and comments

- Use 2 spaces in `.ui` or `.xml` files.
- Good comments explain *why* the code does what it does. If a comment explains
*what* it does, the comment is useless, or the code is bad. (useless comments
are fine, don't worry)
- Upon translatable strings, comments explaining the context to translators are
welcome.

**In python code only:**

- Use actual tabs (4 columns wide).
- Try to not write lines longer than 80 characters.
- Use double quotes for strings the user might see, and single quotes otherwise
(paths, constants, enumerations, dict keys, …)

# Settings

The settings are managed by the `Gio.Settings` abstraction, which will probably
corresponds to the `dconf` database once the app is installed as a native
package.

With flatpak however, which includes the recommended development setup, the
settings are stored in a key-value file, which can be found (and edited) at
`~/.var/app/com.github.maoschanz.drawing/config/glib-2.0/settings/keyfile`.

----

# Structure of the code

The `data` directory contains data useful for installation but useless to the
execution (app icons, desktop launcher, settings schemas, appdata, …).

According to some people, this directory should contain the UI resources, but
here no: resources used by the app (`.ui` files, in-app icons, …) are in `src`,
along with the python code.

>See [here](./design-general.md) for explanations about the architecture and
class diagrams

----

# UI design

If you want to change something to the user interface:

### About Glade

People sometimes like to design their apps in Glade, or in the "GUI designer"
extension integrated in GNOME Builder.

But in Drawing, the UI is modular, and the `.ui` files are mere templates filled
algorithmically according to the user's actions and settings. So you have to:

- edit them with a text editor, since the point of a given file is hard to
understand by just looking at the Glade preview;
- run the app to be sure of how your changes to these files actually look like
once filled with the accurate widgets.

If you **ever** even try to use Glade or a similar software, the auto-generated
code will re-order all the lines, and add dozens of useless properties. Such a
commit diff would be unreadable.

Glade also removes all comments, which are essential to the understanding of the
code, to the generation of the translation files, or which may be disabled code
for future features. It also removes some of the empty containers meant to be
filled by the python code, thus breaking the app.

Please do not use Glade here. Merge requests with such changes will be rejected.

### Guidelines

Try to respect [GNOME Human Interface Guidelines](https://developer.gnome.org/hig/stable/)
as much as possible, while making your feature available from the menubar
(in `app-menus.ui`). The menubar is hidden in most cases, but it should contains
as many `GAction`s as possible for testing purposes (and also because searchable
menus still exist).

If you're contributing to an alternative layout ("elementary OS", "Cinnamon", or
any other), please be sure to not hurt the UX of the GNOME layout (since it's
the one used on smartphone, be careful: it has to stay very resizable).

----

# Other remarks

I like `GAction`s and i've added wrapper methods for using them, try to use that
instead of directly connecting buttons/menu-items to a method.

In my opinion, the difficulties with the code can come mainly from 3 points:

- tools are window-wide, while [the operations they produce](./design-tools#command-pattern),
which are stored in the history, are image-wide.
- the interactions between the tools and the selection manager are ridiculously
complex and numerous _(defining, explicit applying, explicit canceling, import,
clipboard methods, use by the transformation tools (whose operation can be
cancelled or confirmed), deletion, implicit applying, implicit canceling, …)_
which can easily create small bugs or regressions.
- the horizontal and vertical scrollings (and their scrollbars) are managed
"manually" and quite poorly.

These 3 points sometimes can lead to object-oriented spaghetti code.

If you change anything regarding the selection and/or the transformation tools
(which can edit the selection content), make sure to test various scenarios like
this one:

1. several images edited in different tabs of the same window;
2. zoom and/or scroll;
3. select things, or import/paste things (in both tabs);
4. edit the selection (in both tabs, don't forget to click "apply" before
switching to the other tab);
5. unselect it (in both tabs);
6. undo/redo.


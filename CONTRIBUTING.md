# How to contribute to Drawing

----

## If you find a bug

Usability and design issues are considered as bugs.

- If you can, try to check if it hasn't already been fixed.
- Report it with:
	- OS version
	- Flatpak version
	- App version
	- If it's meaningful, screenshots.

----

## If you want a new feature

Usability and design issues are **not** considered as features.

- Report it as an issue, and explain what it does, not how it does it.
- Is it...
	- a general feature ?
	- a new standalone tool ?
	- a new option for an existing tool ? Which one ?

----

## If you want to translate the app

#### I assume this will be the most usual contribution so i detail:

- Fork the repo and clone it on your disk.
- Add your language to `po/LINGUAS`.
- There is probably a more clever way to do, but you can run `./update-translations.sh XX` at the root of the project. Replace `XX` by the actual letters for the language you want. It will produce a `.po` file for your language.
- Use a text editor of [an adequate app](https://flathub.org/apps/details/org.gnome.Gtranslator) to translate the strings of this `.po` file. Do not translate the app id (`com.github.maoschanz.Drawing`).
- If you want to test your translation: GNOME Builder isn't able to run a translated version of the app so export it as a `.flatpak` file and install it.
- Run
```
git add .
git commit
git push
```
And submit a "pull request"/"merge request".

----

## If you want to fix a bug or to add a new feature

- The issue has to be reported first.
- Tell on the issue that you'll do a patch.
- Use tabs in `.py` files.
- Use 2 spaces in `.ui` or `.xml` files.
- Concerning design, try to respect GNOME Human Interface Guidelines as much as possible, while making your feature available from the global menubar.
- I like `GAction`s and i've added wrapper methods for using them, try to use that instead of directly connecting buttons/menu-items to a method.
- If you find some bullshit in the code, or don't understand it, feel free to ask me about it.

----

#### And thank you for caring about this app!


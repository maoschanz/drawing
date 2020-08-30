
<!-- This is the template for adding or updating a translation -->






----

Before opening the merge request, you should check the following points (delete
the text if everything's fine):

## If you added a new language

* The id of your language has been added to the `po/LINGUAS` file

## Crediting

* Is "translator-credits" translated by the complete list of translators
names (optionally with email address)? (one translator per line)
* Proper names should stay untranslated
* You can credit yourself in the README (or, if it's already there, you can
update the translation's completion percentage)

## Keywords

* In the list of keywords used to find the app ("Paint;Sketch;Pencil;"), you
can translate all the keywords and even add a few ones, but "Paint" has to be
present in english so people will find the app when they search for a clone of
MS Paint in their appstore.
* In the list of keywords used to find the app ("Paint;Sketch;Pencil;"), there
has to be a semicolon after each keyword (including the last one!)

## Special formats

* When a string includes "%s", it means there will be a replacement of this
"%s" in the code. Comments are usually included to provide a context. The
replacement is often a file name, or a numerical value. "%%" is the notation for
the symbol "%" itself.

Despite not being shown by default, a menubar exists in this app. When it is
visible, its menus are accessible using keyboard accelerators: `Alt+f` to open
the "_File" menu, `Alt+e` to open the "_Edit" menu, etc.
When you translate the labels of these menus, the "_" character should never be
twice before the same character.

<!-- Example in french:

if "_View" and "_Help" were translated as "_Affichage" and "_Aide", `Alt+a`
would open… nothing at all! The underscore doesn't have to be always before the
first letter: "_Affichage" and "A_ide" are a correct translation.

If your language doesn't use the roman alphabet, you can translate "_File" as
"[your translation of the word File] (_F)"
-->

* Underscore accelerators are available in your translation
* They're never twice on the same key



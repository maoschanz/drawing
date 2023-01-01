
# The tools

>See tools-class-diagram.dia

The tools are managed by a bunch of files in the `src/tools` directory.

## State pattern

>The relationship between the window and the tools is a
**[State](https://en.wikipedia.org/wiki/State_pattern)** design pattern.

>All tools inherit from **abstract** classes defining empty methods. Then, the
active tool's methods are called from the currently active image's code (or the
window's code) regardless of what tool is active.

First of all, `src/tools/abstract_tool.py` defines how the tool will be added in
the UI, provides several wrappers to add options, to access the pixbufs, to add
an operation to the edition history, etc.

The main thing here are the methods that react to clicks on the canvas (starting
a click, moving the pointer, releasing the click).

Then, an other layer of abstract classes is used, depending on the subcategory a
tool is in:

#### Classic tools

These tools draw on the main pixbuf using **`cairo`**, though it can be more
complex.

`abstract_classic_tool.py` manages only a few things like anti-aliasing, and
setting what color is the main or the secondary one depending on the selected
colors and the mouse button you clicked.

#### Selection tools

They translates the user's input into operations using the image's
**selection_manager**. These operations are quite complex, and are almost
entirely managed in `abstract_select.py`.

#### Transformation tools

They (scale/crop/rotate/filters/…) can be applied to the selection pixbuf or the
main pixbuf, and may use the image's `temp_pixbuf` attribute to store a preview
of their changes. These tools have to be explicitly applied by the user, using
a button in the [bottom bar](./design-optionsbars.md).

`abstract_transform_tool.py` defines methods to preview and apply the changes.

----

Other shared features, when they don't depend on the image or the tool at all
(such as blurring, computing some paths, displaying an overlay on the image (for
the selection for example)), may be provided by one of the
`src/tools/utilities_*.py` files.

## Command pattern

>The relationship between the history and the tools is probably an incorrect
**[Command](https://en.wikipedia.org/wiki/Command_pattern)** design pattern.

All code triggered by a click will "end" by a method building a dict (an
associative array) where the value of the key `tool_id` is the id of the tool
building the dict, and the other values tell how to draw whatever the tool is
supposed to draw.

This dict is internally named an "operation". If the operation should be applied
*(e.g. the click to draw a line with the pencil is released)*, the method
`apply_operation` is invoked (by the tool itself…) and it:

- executes the operation on the image (whose `cairo.Surface` is, i suppose, the
receiver in this design pattern);
- adds the operation dict to [the image](./design-general.md) editing history.
The history may invoke `apply_operation` again later, if the user undoes and
redoes operations.

If the operation should **not** be applied, the tool may run code to execute it
directly *(e.g. preview a line while the click isn't released yet)*. In this
case, the surface will be cleaned from the previewed bullshit before seriously
applying the final operation.


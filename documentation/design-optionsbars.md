
# The bottom bar

>See bottombar-class-diagram.dia

Each tool is associated to a bottom bar, providing access the tool's options.
They're named "optionsbar(s)" in the code, and are managed mostly by the
window's **"options manager"**.

Several tools can share the same bottom bar, so the optionsbars are distinct
from the tools. Although both work according to a "state" pattern.

While tools are mostly defining the way the image will behave depending on the
user input, optionsbars also define actual GTK widgets, which have to be
responsive (adapt to mobile phones' window size).

They also have to list options (of course) and actions depending on the current
tool, respond to a few keyboard shortcuts (<kbd>Ctrl</kbd>+<kbd>M</kbd>,
<kbd>Shift</kbd>+<kbd>F10</kbd>, …), and -when it's pertinent- they should
provide access to the minimap and/or the zoom controls.

## Classic optionsbar

the distinctive feature here is the pair of color picking popovers. The default
associated set of options and actions is pretty rich (color, size, cairo
operator, zoom controls, …) and the tools each provide a `Gio.MenuModel` to plug
here, with their specific options.

## Selection optionsbar

all selection tools have roughly the same actions, which are hardcoded in the
optionsbar, although tools can disable actions they don't support (e.g. "Closing
selection", useless for the rectangle selection).

## Transformation tools

each of these tools defines its own optionsbar. All of them have a layout with a
"cancel" button at the left and an "apply" button at the right. The rest can
differ greatly, but it's usually spinbuttons to provide precise control over
numerical values (sizes, angles, percentages, …) in the middle, and a small menu
with options at the right.


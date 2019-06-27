# Install of the unstable version from `master`

## Run as flatpak with GNOME Builder (recommended)

- Clone this repo and open it as a project with GNOME Builder
- Be sure the runtime is installed
- Run it (or export it as a `.flatpak` bundle)

## Install on your system with meson

Dependencies:

| Distribution | Package names | Packages for building |
|--------------|---------------|-----------------------|
| Debian       | `python3-gi python3-gi-cairo gir1.2-gtk-3.0` | `meson` |
| ...          | `???` | `meson` |

(feel free to correct/complete)

```
git clone https://github.com/maoschanz/drawing.git
cd drawing
meson _build
cd _build
ninja
sudo ninja install
```

## With flatpak-builder (not recommended, that's just for me)

Initial installation:
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

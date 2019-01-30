# Install of the unstable version from `master`

## Install on your system with meson

```
git clone https://github.com/maoschanz/drawing.git
cd drawing-master
meson _build
cd _build
ninja
sudo ninja install
```

## With GNOME Builder

Clone this repo, open it as a project with GNOME Builder, and run it (or export it as flatpak)

## With flatpak-builder

Initial installation:
```
wget https://raw.githubusercontent.com/maoschanz/drawing/master/com.github.maoschanz.Drawing.json
flatpak-builder --force-clean _build2/ --repo=_repo com.github.maoschanz.Drawing.json
flatpak --user remote-add --no-gpg-verify local-drawing-repo _repo
flatpak --user install local-drawing-repo com.github.maoschanz.Drawing
```

Update:
```
flatpak-builder --force-clean _build2/ --repo=_repo com.github.maoschanz.Drawing.json
flatpak update
```

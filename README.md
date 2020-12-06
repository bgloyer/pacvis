# pacvis

Visualize pacman local database using [Vis.js](http://visjs.org/),
inspired by [pacgraph](http://kmkeen.com/pacgraph/).

See my blog post for details: https://farseerfc.me/en/pacvis.html

以及中文介紹: https://farseerfc.me/pacvis.html

See a live demo at https://pacvis.farseerfc.me/ showing database of my arch server.

![full](https://img.vim-cn.com/4d/90105c750704af4d586d42be9d10ebe3aa3ded.png)
![zoomin](https://img.vim-cn.com/c7/1c2d03e238e44f70a9ace3fc1975cd6f90a645.png)

## How to use

Install from AUR using any aurhelper (eg `yaourt`):
```bash
yaourt -S pacvis-git
```

Then

```bash
pacvis
```

Then go to http://localhost:8888/ .

You may need to zoom-in initially to see the rendered picture.
~~Currently, we have scalability issue when there are too many packages, so we need
a `max level` to limit the level of dependency depth.~~ We fixed the scalability
issue with a modified vis.js, but when there are more than 2000 packages the
layout algorithm is still slow (more than 5 mins).

## Running from source repo

```bash
git clone https://github.com/farseerfc/pacvis.git
cd pacvis

python -m venv .venv
source .venv/bin/activate

pip install .
pacvis
```

## To be improved ...

- [ ] performance for layout algorithm can be improved
- [ ] we resolve dependency to package name using pyalpm directly now,
      and this information is lost on the graph
- [x] ~~we do not track optdepends now~~
      we draw optdepends on the graph but not consider them during topology_sort
- [x] ~~we need to estimate removable size (by `pacman -Rcs`)~~ done
- [x] more information from pacman can be integrated
- [x] search by package name
- [ ] show only part of the packages (like `pactree`) instead of filtering by levels
- [x] ~~be visually attractive!~~ applied getmdl theme
- [ ] be compatible with older browsers (Safari, IE)
- [x] ~~make a `python setup.py install` or `PKGBUILD`~~ Now on [aur](https://aur.archlinux.org/packages/pacvis-git/)

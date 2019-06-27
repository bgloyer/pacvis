# pacvis

Adpted PacVis from Arch Linux for Gentoo

Cloned from [pacvis](https://github.com/farseerfc/pacvis.git)


Visualize pacman local database using [Vis.js](http://visjs.org/),
inspired by [pacgraph](http://kmkeen.com/pacgraph/).



You may need to zoom-in initially to see the rendered picture.
~~Currently, we have scalability issue when there are too many packages, so we need
a `max level` to limit the level of dependency depth.~~ We fixed the scalability
issue with a modified vis.js, but when there are more than 2000 packages the
layout algorithm is still slow (more than 5 mins).

## Running from source repo

```bash
git clone https://github.com/bgloyer/pacvis.git
cd pacvis
python -m pacvis.pacvis
```

Then go to http://localhost:8888/ .


## To be improved ...

- [ ] make ebuild
- [ ] performance for layout algorithm can be improved
- [x] search by package name
- [ ] show only part of the packages (like `pactree`) instead of filtering by levels
- [x] ~~be visually attractive!~~ applied getmdl theme
- [ ] be compatible with older browsers (Safari, IE)

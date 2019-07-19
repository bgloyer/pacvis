# pacvis

Adpted PacVis from Arch Linux for Gentoo

Cloned from [pacvis](https://github.com/farseerfc/pacvis.git)


Visualize the portage tree

## Running from source repo

```bash
git clone https://github.com/bgloyer/pacvis.git
cd pacvis
python -m pacvis.pacvis
```

Then go to http://localhost:8888/ .

## Changes from parent Arch repo
* Pulled the tree from Poratage (the tree that depclean uses) 
* Added search by partial package name
* Added new topology sort that handles cycles better

## To be improved ...

- [ ] make ebuild
- [x] search by package name
- [ ] show only part of the packages - preveiw what emerge would do

import portage
from portage import os

from _emerge.depgraph import backtrack_depgraph, depgraph, resume_depgraph
from _emerge.actions import load_emerge_config
from _emerge.main import parse_opts
from _emerge.Package import Package
from _emerge.create_depgraph_params import create_depgraph_params
from portage._sets.files import StaticFileSet, WorldSelectedPackagesSet

from .console import start_message, append_message, print_message
portage._internal_caller = True


def printpkg(pkginfo):
    print(pkginfo.name)
    print("deps")
    print(len(pkginfo.deps))
    print(pkginfo.deps)
    print(len(pkginfo.requiredby))
    print(pkginfo.requiredby)

'''
def buildpackagegraph(dbinfo, atoms, digraph, node):
    if isinstance(node, Package):
        nodename = node.cpv
        reponame = node.repo
        if nodename in dbinfo.all_pkgs:
            return dbinfo.all_pkgs[nodename]
    else:
        nodename = f'{node}'
        print(f'{type(node)}:{nodename}')
        reponame = ""
        
    pkg = PkgInfo(nodename, dbinfo)
    pkg.repo = reponame
    selected = nodename == '@selected'
    atoms.append(pkg)
    for child in digraph.child_nodes(node):
        if isinstance(child, Package):
            childname = child.cpv
        else:
            childname = f'{child}'
            
        pkg.deps.append(childname)
        child_pkg = buildpackagegraph(dbinfo, atoms, digraph, child)
        if child_pkg is not None:
            child_pkg.explicit = selected
            child_pkg.requiredby.append(nodename)
    return pkg
'''


# returns true if this package can be merged (updated)
def ismergepkg(pkg):
    ismerge = isinstance(pkg, Package) and pkg.operation == 'merge'
    return ismerge


class PkgInfo:
    def __init__(self, name, merge=False):
        self.desc = name
        self.deps = []
#        self.bdepends = set()
        self.depends = set()
        self.rdepends = set()
        self.pdepends = set()
#        self.rev_bdepends = set()
        self.rev_depends = set()
        self.rev_rdepends = set()
        self.rev_pdepends = set()
        self.explicit = False
        self.stability = ''
        self.groups = {}
        self.isize = 9999
        self.level = 1
        self.circledeps = []
        self.name = name
        self.optdeps = []
        self.provides = []
        self.repo = ''
        self.requiredby =[]
        self.version = 3
        self._merge = merge
        self._is_system = False

    def find_dependencies(self, pkg):
        pass
##        return deps

    def is_virtual(self):
        return self.name.startswith("virtual/")

    def is_system(self):
        return self._is_system

    def is_set(self):
        return self.name.startswith("@")

    def needs_update(self):
        return self._merge
    

def printDepgraph(depgraph):
    print('depgraph:')
    eroot = depgraph._frozen_config.roots[depgraph._frozen_config.target_root].root
    dc_digraph = depgraph._dynamic_config.digraph
##    dc_digraph.debug_print()
    ##    print(type(depgraph._frozen_config))
    for key in depgraph._frozen_config.trees[eroot]:
        v = depgraph._frozen_config.trees[eroot][key]
        print(f'{key} : {type(v)}')
##        for key2 in v:
##            v2 = v[key2]
##            print(f'{key2} : {type(v2)}')
##            print(f'{key2} : {v2}')
##    vardb = depgraph._frozen_config.trees[eroot]['vartree'].dbapi
##    print(type(vardb))
##    print(len(vardb._cpv_map))
##    for pkg in vardb:
##        print(f'{type(pkg)} {pkg.cpv}')
    portdb = depgraph._frozen_config.trees[eroot]['porttree']
    allportnodes = portdb.getallnodes()
    print(f'num nodes {len(allportnodes)}')
    if len(allportnodes) > 0:
        print(f'firstnode {allportnodes[0]}')

    
class PortageTree:
    def __init__(self, emerge_args):

        self.atoms = []
        if emerge_args is None or len(emerge_args) == 0:
            # show the installed packages
            self.load_installed_graph()
        else:
            # show the graph for 'emerge -p {emerge_args}'
            self.load_update_graph(emerge_args)
        
        # sort the dependent packages
        for pkg in self.atoms:
            pkg.deps.sort()
            pkg.requiredby.sort()

    # load a graph like the one portage uses for a depclean.  It is
    # a graph of all installed packages
    def load_installed_graph(self):
        def all_pkg_filter(pkg):
            return True

        myopts = {'--pretend': True}
        emerge_config = load_emerge_config(action=None, args=[], opts=myopts)
        settings, trees, mtimedb = emerge_config

        myparams = create_depgraph_params(myopts, "remove")
        mydepgraph = depgraph(settings, trees, myopts, myparams, None)
        mydepgraph._complete_graph()

        self.trees = trees
        self.digraph = mydepgraph._dynamic_config.digraph
##        printDepgraph(mydepgraph)
        self.atoms = self.buildpkggraphforupdate(all_pkg_filter)

        if len(self.atoms) == 0:
            # there are no packages to display so exit
            mydepgraph.display_problems()
            raise RuntimeError("No packages to display")

        #for rootnode in mydigraph.root_nodes():
         #   buildpackagegraph(dbinfo, self.atoms, mydigraph, rootnode)

    # load a graph the portage uses for updates
    def load_update_graph(self, emerge_args):
        args = emerge_args.split()
        portage._decode_argv(args)
        myaction, myopts, myfiles = parse_opts(args)
        # always set -p so that portage won't try an do anything
        myopts['--pretend'] = True
        emerge_config = load_emerge_config(action=myaction, args=myfiles, opts=myopts)
        settings, trees, mtimedb = emerge_config

        myparams = create_depgraph_params(myopts, "regen")
        #print(f'myparams {myparams}')
        mydepgraph = depgraph(settings, trees, myopts, myparams, None)

        self.trees = trees
        self.digraph = mydepgraph._dynamic_config.digraph
        success, favorites = mydepgraph.select_files(myfiles)

        self.atoms = self.buildpkggraphforupdate(ismergepkg)

        if len(self.atoms) == 0:
            # there are no packages to display so exit
            mydepgraph.display_problems()
            raise RuntimeError("No packages to display")

    def buildpkggraphforupdate(self, pkgfilter):

        class ChildPkg:
            """Holds a pacakge and the dependency types from its parent"""

            def __init__(self, child):
                self.pkg = child
                self.dep = False
                self.rdep = False
                self.pdep = False

            def add_priorities(self, priorities):
                for priority in priorities:
                    self.dep |= priority.buildtime is True
                    self.rdep |= priority.runtime is True
                    self.pdep |= priority.runtime_post is True

        atomsdict = {}  # keeps packages as they are found
        for pkg in self.digraph.nodes:
            if not isinstance(pkg, Package):
                # skip non-packages like @selected
                continue
            pkg_cpv = pkg.cpv
            children = []  # the list of children that meet the filter
            for child, priorities in self.digraph.nodes[pkg][0].items():
                if pkgfilter(child):
                    child_cpv = child.cpv
                    child_pkg = ChildPkg(child)
                    child_pkg.add_priorities(priorities)
                    children.append(child_pkg)
                    if child_cpv not in atomsdict:
                        atomsdict[child_cpv] = self.make_pkginfo(child)
            if (len(children) > 0) or pkgfilter(pkg):
                # add pkg if it has a child or passes the filter
                if pkg_cpv not in atomsdict:
                    atomsdict[pkg_cpv] = self.make_pkginfo(pkg)

                # add links between parent and child
                parent_pkg = atomsdict[pkg_cpv]
                for childpkg in children:
                    child_cpv = childpkg.pkg.cpv
                    # print(f'{pkg_cpv} -> {child_cpv}')
                    child_pkg = atomsdict[child_cpv]
                    parent_pkg.deps.append(child_cpv)
                    child_pkg.requiredby.append(pkg_cpv)
                    # add deps by type
                    if childpkg.dep:
                        parent_pkg.depends.add(child_cpv)
                        child_pkg.rev_depends.add(pkg_cpv)
                    if childpkg.rdep:
                        parent_pkg.rdepends.add(child_cpv)
                        child_pkg.rev_rdepends.add(pkg_cpv)
                    if childpkg.pdep:
                        parent_pkg.pdepends.add(child_cpv)
                        child_pkg.rev_pdepends.add(pkg_cpv)

        return atomsdict.values()

    def make_pkginfo(self, pkg):
        pkg_info = PkgInfo(pkg.cpv, merge=ismergepkg(pkg))
        pkg_info.repo = pkg.repo
        if '9999' in pkg.version:  ## TODO XXXX correct way to do this?
            pkg_info.stability = 'live'
        elif pkg.stable:
            pkg_info.stability = 'stable'
        else:
            pkg_info.stability = 'test'

        # check if it is a system package
        is_system = False
        for system_atom in self.trees['/'].data['root_config'].setconfig.psets['system']._atoms:
            if system_atom.match(pkg):
                is_system = True;
                break

        pkg_info._is_system = is_system

        return pkg_info

    def packages(self):
        return self.atoms

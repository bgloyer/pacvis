import gentoolkit
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


def buildpkggraphforupdate(dbinfo, digraph):
    # returns true if this package can be merged (updated)
    def ismergepkg(pkg):
        ismerge = isinstance(pkg, Package) and pkg.operation == 'merge'
        return ismerge

    atomsdict = {}
    for pkg in digraph.nodes:
        mergechildren = [] # the list of children that can be merged
        for child in digraph.child_nodes(pkg):
            if ismergepkg(child):
                mergechildren.append(child)
                if not child.cpv in atomsdict:
                    atomsdict[child.cpv] = PkgInfo(child.cpv, dbinfo, merge=True)
        if (len(mergechildren) > 0 and isinstance(pkg, Package)) or ismergepkg(pkg):
            # add pkg if it or a child needs merged
            if pkg.cpv not in atomsdict:
                atomsdict[pkg.cpv] = PkgInfo(pkg.cpv, dbinfo, merge=ismergepkg(pkg))

            # add links between parent and child
            parent_pkg = atomsdict[pkg.cpv]
            for mergechild in mergechildren:
                # print(f'{pkg.cpv} -> {mergechild.cpv}')
                child_pkg = atomsdict[mergechild.cpv]
                parent_pkg.deps.append(mergechild.cpv)
                child_pkg.requiredby.append(pkg.cpv)
    return atomsdict.values()


class PkgInfo:
    def __init__(self, name, dbinfo, merge=False):
        self.desc = name
        dbinfo.all_pkgs[name] = self
        self.deps = []
        self.explicit = False
        self.groups = {}
        self.isize = 9999
        self.level = 1
        self.circledeps = []
        self.name = name
        self.optdeps = []
        self.provides = []
        self.repo = []
        self.requiredby =[]
        self.version = 3
        self._merge = merge

    def find_dependencies(self, pkg):
        pass
##        return deps

    def is_virtual(self):
        return self.name.startswith("virtual/")

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
    def __init__(self, dbinfo, emerge_args):

        self.atoms = []
        if emerge_args is None:
            # show the installed packages
            self.load_installed_graph(dbinfo)
        else:
            # show the graph for 'emerge -p {emerge_args}'
            self.load_update_graph(dbinfo, emerge_args)
        
        # sort the dependent packages
        for pkg in self.atoms:
            pkg.deps.sort()
            pkg.requiredby.sort()

    # load a graph like the one portage uses for a depclean.  It is
    # a graph of all installed packages
    def load_installed_graph(self, dbinfo):

        myaction, myopts, myfiles = parse_opts(["-p", "gcc"])
        emerge_config = load_emerge_config(action=myaction, args=myfiles, opts=myopts)
        settings, trees, mtimedb = emerge_config

        myparams = create_depgraph_params(myopts, "remove")
        mydepgraph = depgraph(settings, trees, myopts, myparams, None)
        mydepgraph._complete_graph()
        mydigraph = mydepgraph._dynamic_config.digraph
##        printDepgraph(mydepgraph)

        for rootnode in mydigraph.root_nodes():
            buildpackagegraph(dbinfo, self.atoms, mydigraph, rootnode)

    # load a graph the portage uses for updates
    def load_update_graph(self, dbinfo, emerge_args):
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

        mydigraph = mydepgraph._dynamic_config.digraph
        success, favorites = mydepgraph.select_files(myfiles)
        #mydepgraph.display_problems()

        self.atoms = buildpkggraphforupdate(dbinfo, mydigraph)


    def packages(self):
        return self.atoms

import gentoolkit
import portage
portage._internal_caller = True
from portage import os

from _emerge.depgraph import backtrack_depgraph, depgraph, resume_depgraph
from _emerge.actions import load_emerge_config
from _emerge.main import parse_opts
from _emerge.Package import Package
from _emerge.create_depgraph_params import create_depgraph_params
from portage._sets.files import StaticFileSet, WorldSelectedPackagesSet

from .console import start_message, append_message, print_message


def printpkg(pkginfo):
    print(pkginfo.name)
    print("deps")
    print(len(pkginfo.deps))
    print(pkginfo.deps)
    print(len(pkginfo.requiredby))
    print(pkginfo.requiredby)



def buildpackagetree(dbinfo, atoms, digraph, node):
    if isinstance(node, Package):
        nodename = node.cpv
        reponame = node.repo
        if nodename in dbinfo.all_pkgs:
#            print(f'alread have{nodename}')
            return dbinfo.all_pkgs[nodename]
    else:
        nodename = f'{node}'
        print(f'{type(node)}:{nodename}')
        reponame = ""
        
    pkg = PkgInfo(nodename, dbinfo)
    pkg.repo=reponame
    selected = nodename == '@selected'
    atoms.append(pkg)
    for child in digraph.child_nodes(node):
        if isinstance(child, Package):
            childname = child.cpv
        else:
            childname = f'{child}'
            
        pkg.deps.append(childname)
        child_pkg = buildpackagetree(dbinfo, atoms, digraph, child)
        if child_pkg is not None:
            child_pkg.explicit = selected
##            print("child_pkg")
##            print(nodename)
            child_pkg.requiredby.append(nodename)
        else:
            print(f'zzzzz{child_pkg}')
#    printpkg(pkg)
    return pkg

def buildpkgtreeforupdate(dbinfo, digraph):
    def ismergepkg(pkg):
        ismerge = isinstance(pkg, Package) and pkg.operation == 'merge'
        return ismerge
    atomsdict = {}
    for pkg in digraph.nodes:
        mergechildren = []
        for child in digraph.child_nodes(pkg):
            if ismergepkg(pkg):
                mergechildren.append(child)
                if not child.cpv in atomsdict:
                    atomsdict[child.cpv] = PkgInfo(child.cpv, dbinfo)
        if len(mergechildren) > 0 or ismergepkg(pkg):
            # add pkg if it or a child needs merged
            if not pkg.cpv in atomsdict:
                atomsdict[pkg.cpv] = PkgInfo(pkg.cpv, dbinfo)

            # add links between parent and child
            parent_pkg = atomsdict[pkg.cpv]
            for mergechild in mergechildren:
                # print(f'{pkg.cpv} -> {mergechild.cpv}')
                child_pkg = atomsdict[mergechild.cpv]
                parent_pkg.deps.append(mergechild.cpv)
                child_pkg.requiredby.append(pkg.cpv)
    return atomsdict.values()


class PkgInfo:
    def __init__(self, name, dbinfo):
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
    def find_dependencies(self, pkg):
        pass
##        return deps
    def is_virtual(self):
        return self.name.startswith("virtual/")
    def is_set(self):
        return self.name.startswith("@")
    

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
    def __init__(self, dbinfo):

        
        self.atoms = []
        self.load_installed_tree(dbinfo)
#        self.load_update_tree(dbinfo)
        

        # sort the depenent packages
        for pkg in self.atoms:
            pkg.deps.sort()
            pkg.requiredby.sort()

        
        return
        
        #        myaction, myopts, myfiles = parse_opts(["-p", "--emptytree", "@world"])
        myaction, myopts, myfiles = parse_opts(["-p", "@world"])
        emerge_config = load_emerge_config(action=myaction, args=myfiles, opts=myopts)
##        emerge_config = load_emerge_config(action=myaction, args=myfiles, trees=trees, opts=myopts)
##       	adjust_configs(emerge_config.opts, emerge_config.trees)
        settings, trees, mtimedb = emerge_config
        myopts = emerge_config.opts
        myaction = emerge_config.action
        myfiles = emerge_config.args
        spinner = None

        myparams = create_depgraph_params(myopts, "remove")
        mydepgraph = depgraph(settings, trees, myopts, myparams, spinner)
##        myparams = {} ##XXXX
##        success, mydepgraph, favorites = backtrack_depgraph(
##				settings, trees, myopts, myparams, myaction, myfiles, spinner)
#        mydepgraph._dynamic_config.digraph.debug_print()

        print(f'frozen trees: {len(mydepgraph._frozen_config.trees)}')
##        printDepgraph(mydepgraph)
        mydepgraph._complete_graph()
##        mydepgraph._load_vdb()
##        printDepgraph(mydepgraph)
        


        self.atoms = []
        mydigraph = mydepgraph._dynamic_config.digraph

##        for aaanode in mydigraph.allnodes():
##            print(type(aaanode))
            
        
        for rootnode in mydigraph.root_nodes():
            print("boo")
            print(type(rootnode))
            print(type(rootnode.arg))
            print(rootnode.arg)
            buildpackagetree(dbinfo, self.atoms, mydigraph, rootnode)            
            '''
            for child in mydigraph.child_nodes(rootnode):
                for grandchild in mydigraph.child_nodes(child):
                    grandchildpkg = buildpackagetree(dbinfo, self.atoms, mydigraph, grandchild)
##                    if grandchildpkg:
##                        grandchildpkg.explicit = True
'''

##get worldfile
##        eroot = portage.settings['EROOT']
##        world_set = WorldSelectedPackagesSet(eroot)
##        world_set.load()
##        for worldatom in world_set.getAtoms():
##            print(worldatom.cpv) ## these only have .cp
            ##worldpkg = dbinfo.all_pkgs[worldatom.cpv]
            ##worldpkg.explicit = true

        # sort the depenent packages
        for pkg in self.atoms:
            pkg.deps.sort()
            pkg.requiredby.sort()

    # load a graph like the one portage uses for a depclean.  It is
    # a tree of all installed packages
    def load_installed_tree(self, dbinfo):

        myaction, myopts, myfiles = parse_opts(["-p", "gcc"])
        emerge_config = load_emerge_config(action=myaction, args=myfiles, opts=myopts)
        settings, trees, mtimedb = emerge_config

        myparams = create_depgraph_params(myopts, "remove")
        mydepgraph = depgraph(settings, trees, myopts, myparams, None)
        mydepgraph._complete_graph()
        mydigraph = mydepgraph._dynamic_config.digraph
##        printDepgraph(mydepgraph)

        
        for rootnode in mydigraph.root_nodes():
            buildpackagetree(dbinfo, self.atoms, mydigraph, rootnode)            

    # load a graph the portage uses for updates
    def load_update_tree(self, dbinfo):

        myaction, myopts, myfiles = parse_opts(["-p", "@world"])
        emerge_config = load_emerge_config(action=myaction, args=myfiles, opts=myopts)
        settings, trees, mtimedb = emerge_config

        myparams = create_depgraph_params(myopts, "regen")
        print(f'myparams {myparams}')
        mydepgraph = depgraph(settings, trees, myopts, myparams, None)

        mydigraph = mydepgraph._dynamic_config.digraph
        success, favorites = mydepgraph.select_files(myfiles)
        #mydepgraph.display_problems()

        self.atoms = buildpkgtreeforupdate(dbinfo, mydigraph)


    def packages(self):
        return self.atoms

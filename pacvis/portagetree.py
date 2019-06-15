#from itertools import groupby
#import math
#import re

import gentoolkit
import portage
portage._internal_caller = True
from portage import os

from _emerge.depgraph import backtrack_depgraph, depgraph, resume_depgraph
from _emerge.actions import load_emerge_config
from _emerge.main import parse_opts
from _emerge.Package import Package
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
##    print(type(node))
##    print(node.cpv)
    if isinstance(node, Package):
        nodename = node.cpv
        reponame = node.repo
        if nodename in dbinfo.all_pkgs:
            print(f'alread have{nodename}')
            return dbinfo.all_pkgs[nodename]
    else:
        nodename = f'{node}'
        print(f'{type(node)}:{nodename}')
        reponame = ""
        
##    print(nodename)
    pkg = PkgInfo(nodename, dbinfo)
    pkg.repo=reponame
    atoms.append(pkg)
    for child in digraph.child_nodes(node):
        if isinstance(child, Package):
            childname = child.cpv
        else:
            childname = f'{child}'
            
        pkg.deps.append(childname)
##        print(childname)
##        print(pkg.deps)
        child_pkg = buildpackagetree(dbinfo, atoms, digraph, child)
        if child_pkg is not None:
            print("child_pkg")
            print(nodename)
            child_pkg.requiredby.append(nodename)
        else:
            print(f'zzzzz{child_pkg}')
    printpkg(pkg)
    return pkg
    
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

    
class PortageTree:
    def __init__(self, dbinfo):
        myaction, myopts, myfiles = parse_opts(["-p", "--emptytree", "@world"])
        emerge_config = load_emerge_config(action=myaction, args=myfiles, opts=myopts)
##        emerge_config = load_emerge_config(action=myaction, args=myfiles, trees=trees, opts=myopts)
##       	adjust_configs(emerge_config.opts, emerge_config.trees)
        settings, trees, mtimedb = emerge_config
        myopts = emerge_config.opts
        myaction = emerge_config.action
        myfiles = emerge_config.args
        spinner = None
        myparams = {} ##XXXX
        
        success, mydepgraph, favorites = backtrack_depgraph(
				settings, trees, myopts, myparams, myaction, myfiles, spinner)
#        mydepgraph._dynamic_config.digraph.debug_print()

        


        self.atoms = []
        mydigraph = mydepgraph._dynamic_config.digraph

        for aaanode in mydigraph.allnodes():
            print(type(aaanode))
            
        
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

    def packages(self):
        return self.atoms
    
        
        
        

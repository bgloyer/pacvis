from itertools import groupby
import math
import re

from .portagetree import PkgInfo, PortageTree

from .console import start_message, append_message, print_message



class DbInfo:
    def __init__(self):
        self.handle = {} #pycman.config.init_with_config("/etc/pacman.conf")
        self.localdb = {"xxxxx"} #self.handle.get_localdb()
        self.syncdbs = {} #self.handle.get_syncdbs()
        self.packages = {}  #{PkgInfo("pppp", "dbinfo") } #self.localdb.pkgcache
        self.all_pkgs = {}
        self.groups = {}
        self.repos = {}
        self.vdeps = {}
        self.repo_list = [] #[x.name for x in self.syncdbs]
        local = "XXXX" #self.localdb.name
        self.repo_list.append(local)
        self.repos[local] = RepoInfo(local, self)
#        print_message("Enabled repos: %s" %
#                      ", ".join(db.name for db in self.syncdbs))
#        tree = PortageTree(self)
#        self.packages = tree.packages()

        print_message("Repo_list repos: %s" % ", ".join(self.repo_list))

    def find_syncdb(self, pkgname):
        repo = ""
        found = False
        for db in self.syncdbs:
            if db.get_pkg(pkgname) is not None:
                found = True
                repo = db.name
                break
        if not found:
            repo = self.localdb.name
        if repo not in self.repos:
            self.repos[repo] = RepoInfo(repo, self)
        self.repos[repo].add_pkg(pkgname)
        return repo

    def get(self, pkgname):
        return self.all_pkgs[pkgname]

    def resolve_dependency(self, dep):
        pkgname = self.requirement2pkgname(dep)
        if dep in self.all_pkgs:
            return dep
        pkg = pyalpm.find_satisfier(self.packages, dep)
        if pkg is None:
            return None
        return pkg.name

    def find_all(self, showallvdeps):
        if len(self.packages) == 0:
            tree = PortageTree(self)
            self.packages = tree.packages()
        return self.all_pkgs

    '''
        for pkg in self.packages:
            PkgInfo(pkg.name, self)
        for pkg in self.all_pkgs.values():
            pkg.find_dependencies(self)
        if showallvdeps:
            return self.all_pkgs
        # remove vdeps without requiredby
        for pkg in list(self.all_pkgs.values()):
            if type(pkg) is VDepInfo:
                if len(pkg.requiredby) == 0:
                    for dep in pkg.deps:
                        while pkg.name in self.get(dep).requiredby:
                            self.get(dep).requiredby.remove(pkg.name)
                    while pkg.repo in self.repos and pkg.name in self.repos[pkg.repo].pkgs:
                        self.repos[pkg.repo].pkgs.remove(pkg.name)
                    del self.all_pkgs[pkg.name]
                    del self.vdeps[pkg.name]
'''
    def find_circles(self):
        return ## XXXX try skipping
        """ https://zh.wikipedia.org/wiki/Tarjan%E7%AE%97%E6%B3%95 """
        stack = list()
        indexes = dict()
        lowlinks = dict()
        index = 0

        def strongconnect(pkg):
            nonlocal stack, indexes, lowlinks, index
            indexes[pkg] = index
            lowlinks[pkg] = index
            index += 1
            stack.append(pkg)
            for dep in self.get(pkg).deps:
                if dep not in indexes:
                    strongconnect(dep)
                    lowlinks[pkg] = min(lowlinks[pkg], lowlinks[dep])
                elif dep in stack:
                    lowlinks[pkg] = min(lowlinks[pkg], indexes[dep])
            if lowlinks[pkg] == indexes[pkg]:
                cirdeps = []
                while True:
                    w = stack.pop()
                    cirdeps.append(w)
                    if (w == pkg):
                        break
                self.get(pkg).circledeps = cirdeps

        for pkg in self.all_pkgs:
            if pkg not in indexes:
                strongconnect(pkg)
        numcircles = 0
        for pkg in self.all_pkgs:
            circleLen = len(self.get(pkg).circledeps) 
            if circleLen > 1:
                numcircles = numcircles + 1
                print (circleLen)
        print(f'num cycles {numcircles}')

    def top_down_sort(self, usemagic, all_pkgs):
        remain_pkgs = set(all_pkgs)
        cycle_check = set()
        start_message("Top-down sorting ")
        # put all of the @system package on top
        for pkg in all_pkgs:
            pkginfo = self.get(pkg)
            if '@system' in pkginfo.requiredby:
                print(f'@system {pkginfo.name}')
                pkginfo.level = 0
                remain_pkgs.remove(pkg)
                
        while len(remain_pkgs) > 0:
            pkg = remain_pkgs.pop()
            pkginfo = self.get(pkg)
            origin_level = pkginfo.level
            print("%s %d (remaining %d)" % (pkg,
                                                     origin_level,
                                                     len(remain_pkgs)))
            if len(all_pkgs.intersection(pkginfo.deps)) == 0:
                if all([len(pkginfo.deps) == 0,
                        len(pkginfo.requiredby) == 0]):
                    pkginfo.level = 1 ##  0
                continue
            max_level = 1 + max(self.get(x).level
                                for x in all_pkgs.intersection(pkginfo.deps))
            if usemagic:
                # below is magic
                new_level = max_level + int(math.log(1 +
                                                     len(pkginfo.deps) +
                                                     len(pkginfo.requiredby)))
            else:
                new_level = max_level  # we may not need magic at all
            if new_level != origin_level:
                pkginfo.level = new_level
                #### XXXX loops here
###                remain_pkgs.update(
###                    all_pkgs.intersection(
###                        set(pkginfo.requiredby).difference(
###                            pkginfo.circledeps)))

                update_set = all_pkgs.intersection(
                        set(pkginfo.requiredby).difference(
                            pkginfo.circledeps))
                cycle_check.update(update_set)
                remain_pkgs.update(update_set.difference(cycle_check))
                print(f' level {pkginfo.level} : {origin_level} len: {len(update_set)} rem: {len(remain_pkgs)} name {pkginfo.name}')


    def buttom_up_sort(self, all_pkgs):
        remain_pkgs = set(all_pkgs)
        start_message("Buttom-up sorting ")
        while len(remain_pkgs) > 0:
            pkg = remain_pkgs.pop()
            pkginfo = self.get(pkg)
            origin_level = pkginfo.level
            append_message("%s %d (remaining %d)" % (pkg,
                                                     origin_level,
                                                     len(remain_pkgs)))
            if len(all_pkgs.intersection(pkginfo.requiredby)) == 0:
                continue
            min_level = min(self.get(x).level
                            for x in all_pkgs.intersection(pkginfo.requiredby))
            new_level = min_level - 1
            if new_level > origin_level:
                pkginfo.level = new_level
                remain_pkgs.update(all_pkgs.intersection(set(pkginfo.deps)
                                   .difference(pkginfo.circledeps)))

    def minimize_levels(self, all_pkgs, nextlevel):
        start_message("Minimizing levels ... ")
        pkgs = list(sorted((self.get(pkg) for pkg in all_pkgs),
                           key=lambda x: x.level))
        for key, group in groupby(pkgs, key=lambda x: x.level):
            for pkg in group:
                pkg.level = nextlevel
            nextlevel += 1
        append_message("max available level: %d" % nextlevel)
        return nextlevel

    def calc_repo_average(self):
        result = {}
        for repo in self.repos:
            result[repo] = self.repos[repo].average_level()
        return result

    def topology_sort(self, usemagic, aligntop, byrepos):
        level = 1
        found_level = set()
        found_pkgs = set() ## the packages that have been assigned to a level
        # find the top level packages that nothing depends on
        found_level = list(filter(lambda p: len(self.get(p).requiredby) == 0,
                                  self.all_pkgs))
        next_deps = set()  ## the set of deps of found_pkgs that are not found
        while True:
            for found_pkg in map(lambda pkg_name: self.get(pkg_name), found_level):
                found_pkg.level = level
            level += 1
            found_pkgs.update(found_level)
            ##find the next level of deps
            for found_pkg in map(lambda pkg_name: self.get(pkg_name), found_level):
                next_deps.update(found_pkg.deps)

            ## remove any already in the found set to protect from cycles
            next_deps -= found_pkgs

            ## find the package with the fewest number of dependacies outside
            ## of the found set.  It would be 0 except for cycles
            min_reqby = len(self.all_pkgs)
            reqby_dict = {}
            for dep_name in next_deps:
                req_by = set(self.get(dep_name).requiredby)
                req_by -= found_pkgs
                num_req_by = len(req_by)
                if num_req_by in reqby_dict:
                    reqby_dict[num_req_by].append(dep_name)
                else:
                    reqby_dict[num_req_by] = [dep_name]
                
                min_reqby = min(min_reqby, num_req_by)

            if not min_reqby in reqby_dict:
                ## all package have been placed
                break

            found_level = reqby_dict[min_reqby]
            if min_reqby > 0:
                # find the package with the most deps
                max_deps = -1
                for dep_name in found_level:
                    num_deps = len(self.get(dep_name).deps)
                    if max_deps < num_deps:
                        max_deps = num_deps
                        max_dep_name = dep_name
                found_level = [max_dep_name]
                        
            
            ##print(f'level: {level} min_reqby: {min_reqby} num pkgs: {len(found_level)}')

        self.compress_down()
        self.adjust_up()

    # move all the nodes down to the level above its highest dep
    def compress_down(self):
        sorted_pkgs = sorted(self.all_pkgs, key=lambda pkg: self.get(pkg).level, reverse=True)
        if len(sorted_pkgs) < 1:
            return
        currlevel = self.get(sorted_pkgs[0]).level
        for pkg_name in sorted_pkgs:
            pkg = self.get(pkg_name)
            min_dep_level = 999999
            # find the highest dep below the node, skip ones
            # above the node because they are in cycles
            for pkg_dep in pkg.deps:
                pkg_dep_level = self.get(pkg_dep).level
                if pkg.level < pkg_dep_level:
                    # count this dep because it is above pkg
                    min_dep_level = min(min_dep_level, pkg_dep_level)
            if min_dep_level != 999999:
                assert pkg.level < min_dep_level # dont move the package up
                pkg.level = min_dep_level - 1
                currlevel = pkg.level
            else:
                # there were no deps above this level but make sure not to put
                # 2 packages on the same level
                samereqlevel = False
                for pkg_req in pkg.requiredby:
                    samereqlevel |= currlevel == self.get(pkg_req).level
                if samereqlevel:
                    # this is on the same level as a req by put it up a level
                    # so that they won't be on the same level
                    pkg.level = max(currlevel - 1, pkg.level)
                else:
                    pkg.level = currlevel

        # shift them so the top node starts at 1
        shift = self.get(min(sorted_pkgs, key=lambda x: self.get(x).level)).level - 1
        for pkg_name in sorted_pkgs:
            self.get(pkg_name).level -= shift

    # adjust some packages up to make it look better
    def adjust_up(self):
        for pkg_name in self.all_pkgs:
            pkg = self.get(pkg_name)
            if len(pkg.deps) == 0:
                # adjust package up that have no deps
                max_reqby_level = -1
                for req_name in pkg.requiredby:
                    max_reqby_level = max(max_reqby_level, self.get(req_name).level)
                if max_reqby_level != -1:
                    pkg.level = min(pkg.level, max_reqby_level + 1)
                         
    def topology_sort_orig(self, usemagic, aligntop, byrepos):
        if not byrepos:
            all_pkgs = {x for x in self.all_pkgs}
            self.top_down_sort(usemagic, all_pkgs)
            self.buttom_up_sort(all_pkgs)
            if aligntop:
                # do top_down_sort again to align to top
                self.top_down_sort(usemagic, all_pkgs)
            self.minimize_levels(all_pkgs, 1)
        else:
            nextlevel = 1
            for repo in self.repo_list:
                if repo not in self.repos:
                    continue
                print_message("Repo %s" % repo)
                all_pkgs = self.repos[repo].pkgs
                for pkg in all_pkgs:
                    self.get(pkg).level = nextlevel  # assign initial level
                self.top_down_sort(usemagic, all_pkgs)
                self.buttom_up_sort(all_pkgs)
                if aligntop:
                    # do top_down_sort again to align to top
                    self.top_down_sort(usemagic, all_pkgs)
                nextlevel = self.minimize_levels(all_pkgs, nextlevel)

                
    def calcCSize(self, pkg):
        pkg.csize = 77777
        return pkg.csize
    ''' XXXX TODO keep this?
        removing_pkg = set()

        def remove_pkg(pkgname):
            nonlocal removing_pkg
            removing_pkg.add(pkgname)
            for dep in self.get(pkgname).requiredby:
                if dep not in removing_pkg:
                    remove_pkg(dep)

        remove_pkg(pkg.name)
        pkg.csize = 77777 #sum(self.get(pkg).isize for pkg in removing_pkg)
        append_message("csize %s: %d" % (pkg.name, pkg.csize))
        return pkg.csize
'''
    def calcCsSize(self, pkg):
        pkg.cssize = 88888
        return pkg.cssize
    '''' XXXX keep this?
        removing_pkg = set()
        analyzing_pkg = set()

        def remove_pkg(pkgname):
            nonlocal removing_pkg
            removing_pkg.add(pkgname)
            for dep in self.get(pkgname).deps:
                if not self.get(dep).explicit:
                    analyzing_pkg.add(dep)
            for dep in self.get(pkgname).requiredby:
                if dep not in removing_pkg:
                    remove_pkg(dep)

        remove_pkg(pkg.name)
        while len(analyzing_pkg) > 0:
            apkg = self.get(analyzing_pkg.pop())
            if apkg.name in removing_pkg:
                continue
            if all(dep in removing_pkg for dep in apkg.requiredby):
                remove_pkg(apkg.name)
        pkg.cssize = 88888 #sum(self.get(pkg).isize for pkg in removing_pkg)
        append_message("cssize %s: %d" % (pkg.name, pkg.cssize))
        return pkg.cssize
'''
    def calcSizes(self):
        start_message("Calculating csize ... ")
        maxCSize = max(self.calcCSize(pkg) for pkg in self.all_pkgs.values())
        append_message(" max cSize: " + str(maxCSize))
        start_message("Calculating cssize ... ")
        maxCsSize = max(self.calcCsSize(pkg) for pkg in self.all_pkgs.values())
        append_message(" max csSize: " + str(maxCsSize))

    def requirement2pkgname(self, requirement):
        if any(x in requirement for x in "<=>"):
            return re.split("[<=>]", requirement)[0]
        return requirement

    def find_vdep(self, provide, pkg):
        name = self.requirement2pkgname(provide)
        if name in self.all_pkgs:
            return name
        if name not in self.vdeps:
            VDepInfo(name, self)
        self.vdeps[name].deps.append(pkg)
        self.all_pkgs[pkg].requiredby.append(name)
        return name

"""
class PkgInfo:
    def __init__(self, name, dbinfo):
        self.name = name
        self.pkg = "XxXx" #dbinfo.localdb.get_pkg(name)
        dbinfo.all_pkgs[name] = self
        self.deps = []
        self.requiredby = []
        self.optdeps = []
        self.level = 1
        self.circledeps = []
        self.explicit = 0 == 0 #self.pkg.reason == 0
        self.isize = 56565 #self.pkg.isize
        self.desc = "desc" #self.pkg.desc
        self.version = "v1" #self.pkg.version
        self.repo = "pkginfoRepo" #dbinfo.find_syncdb(self.name)
        self.groups = {} #self.pkg.groups
        self.provides = [] # [dbinfo.find_vdep(pro, self.name)
##                         for pro in self.pkg.provides]
        for grp in self.groups:
            if grp in dbinfo.groups:
                dbinfo.groups[grp].add_pkg(self.name)
            else:
                GroupInfo(grp, dbinfo)
                dbinfo.groups[grp].add_pkg(self.name)

    def find_dependencies(self, dbinfo):
        pass
#        for dep in self.pkg.depends:
#            dependency = dbinfo.resolve_dependency(dep)
#            if dependency in dbinfo.all_pkgs:
#                self.deps.append(dependency)
#                dbinfo.get(dependency).requiredby.append(self.name)
#        for dep in self.pkg.optdepends:
#            depname = dep.split(":")[0]
#            resolved = dbinfo.resolve_dependency(depname)
#            if resolved is not None:
#                self.optdeps.append(resolved)
        # self.requiredby.extend(self.pkg.compute_requiredby())
"""

class GroupInfo (PkgInfo):
    def __init__(self, name, dbinfo):
        self.name = name
        self.deps = []
        self.requiredby = []
        self.optdeps = []
        self.provides = []
        self.level = 1
        self.circledeps = []
        self.groups = []
        self.explicit = True
        self.isize = 0
        self.desc = name + " package group"
        self.version = ""
        self.repo = None
        self.dbinfo = dbinfo
        self.dbinfo.groups[name] = self
        self.dbinfo.all_pkgs[name] = self

    def add_pkg(self, pkgname):
        self.deps.append(pkgname)
        self.dbinfo.get(pkgname).requiredby.append(self.name)

    def reset_repo(self):
        for repo in self.dbinfo.repo_list:
            for pkg in self.deps:
                if self.dbinfo.get(pkg).repo == repo:
                    self.repo = repo
                    self.dbinfo.repos[self.repo].pkgs.add(self.name)
                    return

    def find_dependencies(self, dbinfo):
        self.reset_repo()


class VDepInfo (PkgInfo):
    def __init__(self, name, dbinfo):
        self.name = name
        self.deps = []
        self.requiredby = []
        self.optdeps = []
        self.provides = []
        self.level = 1
        self.circledeps = []
        self.groups = []
        self.explicit = True
        self.isize = 0
        self.desc = name + " virtual dependency"
        self.version = ""
        self.repo = None
        self.dbinfo = dbinfo
        self.dbinfo.all_pkgs[name] = self
        self.dbinfo.vdeps[name] = self

    def reset_repo(self):
        for repo in self.dbinfo.repo_list:
            for pkg in self.deps:
                if self.dbinfo.get(pkg).repo == repo:
                    self.repo = repo
                    self.dbinfo.repos[self.repo].pkgs.add(self.name)
                    return

    def find_dependencies(self, dbinfo):
        self.reset_repo()
        for dep in self.deps:
            dbinfo.get(dep).requiredby.append(self.name)


class RepoInfo:
    def __init__(self, name, dbinfo):
        self.name = name
        self.pkgs = set()
        self.level = -1
        self.dbinfo = dbinfo

    def add_pkg(self, pkgname):
        self.pkgs.add(pkgname)


def test_circle_detection():
    dbinfo = DbInfo()
    start_message("find all packages...")
    dbinfo.find_all()
    append_message("done")
    start_message("find all dependency circles...")
    dbinfo.find_circles()
    append_message("done")
    for name, pkg in dbinfo.all_pkgs.items():
        if len(pkg.circledeps) > 1:
            print_message("%s(%s): %s" %
                          (pkg.name, pkg.circledeps, ", ".join(pkg.deps)))
    dbinfo.topology_sort()
    for pkg in sorted(dbinfo.all_pkgs.values(), key=lambda x: x.level):
        print("%s(%d): %s" % (pkg.name, pkg.level, ", ".join(pkg.deps)))

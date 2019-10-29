#!/usr/bin/env python

import sys
import json
from types import SimpleNamespace
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from webbrowser import open_new_tab

import tornado.ioloop
import tornado.web

from .console import start_message, append_message, print_message
from .infos import DbInfo, PkgInfo, GroupInfo, VDepInfo


# Tornado entry
class MainHandler(tornado.web.RequestHandler):

    @classmethod
    def loadgraph(cls, emerge_args):
        # load the package database
        dbinfo = DbInfo()
        start_message("Loading local database ...")
        dbinfo.load_graph(emerge_args)
#        dbinfo.find_all(False)
        append_message("done")
#        start_message("Finding all dependency circles ... ")
#        dbinfo.find_circles()
#        append_message("done")
        cls.dbinfo = dbinfo

    def parse_args(self, **kargs):
        result = {}
        for key in kargs:
            defvalue = str(kargs[key])
            if type(kargs[key]) is int:
                result[key] = int(self.get_argument(key, defvalue))
            elif type(kargs[key]) is bool:
                result[key] = self.get_argument(key, defvalue) != "False"
            else:
                result[key] = self.get_argument(key, defvalue)
#            print_message("get arg %r: %r" % (key, result[key]))
        return result

    def get(self):
 #       print_message("\n" + str(self.request))
        args = SimpleNamespace(**self.parse_args(
            maxlevel=1000,
            maxreqs=1000,
            maxdeps=1000,
            drawsize="isize",
            usemagic=False,
            straightline=False,
            enablephysics=False,
            aligntop=False,
            disableallphysics=False,
            debugperformance=False,
            byrepos=False,
            showallvdeps=False))
        dbinfo = MainHandler.dbinfo
        dbinfo.topology_sort(args.usemagic, args.aligntop, args.byrepos)
        dbinfo.calcSizes()

#        start_message("Rendering ... ")

        nodes = []
        links = []

        ids = 0
        for pkg in sorted(dbinfo.all_pkgs.values(), key=lambda x: x.level):
#            append_message("%s" % pkg.name)
            pkg.id = ids
            ids += 1
            if pkg.level < args.maxlevel:
                catagory = "normal"
                if pkg.explicit:
                    catagory = 'explicit' # selected
                elif pkg.is_system(): # TODO XXXX
                    catagory = 'system'
                elif pkg.is_virtual():
                    catagory = 'virtual'
                elif pkg.is_set():
                    catagory = 'set'

                build_status = 'keep'
                if pkg.needs_update():
                    build_status = 'update' # TODO XXXX show as remove then add?
                '''
                elif ids % 7 == 0:
                    if ids % 4 == 0:
                        build_status = 'add'
                    elif ids % 4 == 1:
                        build_status = 'remove'
                    elif ids % 4 == 3:
                        build_status = 'rebuild'
                    else:
                        build_status = 'not_installed' 
'''

                if pkg.repo == 'gentoo':
                    if pkg.stability == 'stable':
                        stability = 'stable'
                    elif pkg.stability == 'test':
                        stability = 'test' #
                    elif pkg.stability == 'live':
                        stability = 'live'
                else:  # this package is from an overlay
                    if pkg.stability == 'live':
                        stability = 'overlay-live'
                    else:
                        stability = 'overlay-test'  # TODO inclulde overlay-stable?

                node = {"id": pkg.id,
                        "label": pkg.name,
                        "level": pkg.level,
                        "catagory": catagory,
                        "build_status": build_status,
                        "stability": stability,
                        "isize": pkg.isize,
                        "csize": pkg.csize,
                        "cssize": pkg.cssize,
                        "deps": ", ".join(pkg.deps),
                        "reqs": ", ".join(pkg.requiredby),
                        "desc": pkg.desc,
                        "version": pkg.version,
                        "repo": pkg.repo,
                }

                nodes.append(node)
        ids = 0
        for pkg in sorted(dbinfo.all_pkgs.values(), key=lambda x: x.level):
            if pkg.level < args.maxlevel:
                # add edges between the node according to the dep type.  Only
                # add the strongest edge if there is more than one between two nodes
                added_deps = set() # to avoid adding two links between the same pair
                if len(pkg.deps) == 0 and len(pkg.requiredby) == 0:
                    links.append({"id": ids,
                                  "from": pkg.id,
                                  "to": 0})
                    ids += 1
                for dep in pkg.depends:
                    link = {"id": ids,
                            "from": pkg.id,
                            "to": dbinfo.get(dep).id,
                            "dep": 'DEPEND'}
                    links.append(link)
                    added_deps.add(dep)
                    ids += 1

                for dep in pkg.rdepends:
                    if dep in added_deps:
                        # this package already has a stronger dep link
                        continue
                    link = {"id": ids,
                            "from": pkg.id,
                            "to": dbinfo.get(dep).id,
                            "dep": 'RDEPEND'}
                    links.append(link)
                    added_deps.add(dep)
                    ids += 1

                for dep in pkg.pdepends:
                    if dep in added_deps:
                        # this package already has a stronger dep link
                        continue
                    link = {"id": ids,
                            "from": pkg.id,
                            "to": dbinfo.get(dep).id,
                            "dep": 'PDEPEND'}
                    links.append(link)
                    ids += 1

        print_message("Writing HTML")
        self.render("templates/index.template.html",
                    nodes=json.dumps(nodes),
                    links=json.dumps(links),
                    options=args,
                    optionsjson=json.dumps(args.__dict__))


def make_app():
    import os
    return tornado.web.Application([
        (r"/", MainHandler),
        ], debug=True,
        static_path=os.path.join(os.path.dirname(__file__), "static"))

def parse_args():
    argp = ArgumentParser(description='start pacvis server', allow_abbrev=False,
                          epilog="arguments after the optional pacvis arguments will be passed on to"
                                 " emerge.  example usage: pacvis -p 8888 -b --update --changed-use --deep @world",
                          formatter_class=ArgumentDefaultsHelpFormatter)
    argp.add_argument('-p', '--port', type=int, default=8888, help='listen at given port')
    argp.add_argument('-s', '--host', type=str, default='localhost', help='listen at given hostname')
    argp.add_argument('-b', '--browser', action='store_true', help='start a browser')

    # remove '-p' (--pretend) and -1' (--oneshot) from argv so it isn't accidentally interpreted as a port number
    adjusted_args = []
    is_prev_positive_int = False
    for arg in reversed(sys.argv[1:]):
        if arg == '-1' or arg == '-p' and not is_prev_positive_int:
            is_prev_positive_int = False
            continue
        try:
            val = int(arg)
            is_prev_positive_int = val > 0
        except ValueError:
            is_prev_positive_int = False
        adjusted_args.append(arg)
    adjusted_args = reversed(adjusted_args)

    args, rest = argp.parse_known_args(adjusted_args)

    emerge_args = ""
    for arg in rest:
        emerge_args += " " + arg

    return args, emerge_args

def main():
    pacvis_args, emerge_args = parse_args()
    try:
        MainHandler.loadgraph(emerge_args)
    except RuntimeError as err:
        print(f'\n{err}')
        sys.exit(0)

    app = make_app()
    app.listen(pacvis_args.port, address=pacvis_args.host)
    print_message(f"Start PacVis at http://{pacvis_args.host}:{pacvis_args.port}/")
    if pacvis_args.browser:
        url = f'http://{pacvis_args.host}:{pacvis_args.port}/'
        print_message(f'open in browser: {url}')
        open_new_tab(url)
    else:
        print_message('use --browser to open a browser automatically.')
    try:
    	tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        print_message("Received interrupt from keyboard, shutting down ...")
        sys.exit(0)


if __name__ == "__main__":
    main()

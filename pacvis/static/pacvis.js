function filesize(size) {
  var units = "KMGT";
  var left = size;
  var unit = -1;
  for (; left > 1100 && unit < 3; unit++) {
    left /= 1024;
  }
  if (unit === -1) {
    return size + "B";
  } else {
    if (size < 0)
      left = -left;
    return Math.round(left * 100) / 100 + units[unit] + "iB";
  }
}

function size2value(size) { return size==0 ? 12 : Math.sqrt(Math.sqrt(size)) / 5; }

function setNodeStyle(node) {
  // set the shape based on catagory
  if (node.catagory == 'normal') {
    node.shape = 'box'
  } else if (node.catagory == 'explicit') {
    node.shape = 'circle'
  } else if (node.catagory == 'system') {
    node.shape = 'ellipse'
  } else if (node.catagory == 'virtual') {
    node.shape = 'triangle'
  } else if (node.catagory == 'set') {
    node.shape = 'database'
  } else {
    node.shape = 'star' // should not happen
  }

  // set color based on add, remove, etc.
  if (node.build_status == "add") {
    node.color = 'rgba(64,64,255,0.8)'
  } else if (node.build_status == "keep") {
    node.color = 'rgba(0,255,0,0.8)'
  } else if (node.build_status == "update") {
    node.color = 'rgba(200,200,0,0.8)'
  } else if (node.build_status == "remove") {
    node.color = 'rgba(245, 94, 0,0.8)'
  } else if (node.build_status == "rebuild") {
    node.color = 'rgba(0, 255, 200 ,0.8)'
  } else if (node.build_status == "not_installed") {
    node.color = 'rgba(166,166,166,0.6)'
  } else { // should not happen
    node.color = 'rgba(255,0,0, 0.98)'
  }

  // use the boarder to indicate arch, ~arch, overlays, etc.
  node.borderWidth = 15;
  if (node.stability == 'stable') {
//    node.color.border = '#66FF77'
//    node.shapeProperties.borderDashes = false;
  } else if (node.stability == 'test') {
//    node.color.border = '#AAFF44'
//    node.shapeProperties.borderDashes = false;
    node.shapeProperties = {borderDashes: true};
  } else if (node.stability == 'live') {
//    node.color.border = '#DDBB77'
    node.shapeProperties = {borderDashes: [4, 12]};
  } else if (node.stability == 'overlay-test') {
 //   node.color.border = '#FF9977'
    node.shapeProperties = {borderDashes: [4, 28]};
  } else if (node.stability == 'overlay-live') {
 //   node.color.border = 'FF4433'
    node.shapeProperties = {borderDashes: [8, 24]};
  }
}

function setEdgeStyle(edge){
  if (edge.dep == "DEPEND"){
    //      edge.color = 'rgba(120,255,100,0.8)'
    //      edge.dashes = [30, 2, 14, 2, 6, 2, 2, 2] //Dashed lines are too slow to draw 
  } else if (edge.dep == "RDEPEND"){
//      edge.color = 'rgba(64,255,200,0.8)'
      edge.dashes = [48, 4, 12, 4, 4, 4]  
  } else if (edge.dep == "PDEPEND"){
//      edge.color = 'rgba(64,64,255,0.8)'  
      edge.dashes = [40, 6, 10, 6, 2, 6, 2, 6]  
  } else { // Should not happen, maybe BDEPEND later
  //  edge.color = 'rgba(24,247,54,0.8)'  
  }
}


function createPkgButton(dep) {
    return "<button class=\"mdl-button mdl-js-button mdl-js-ripple-effect\" onclick='document.getElementById(\"search\").value=\"" +
               dep + "\";trysearch()'>" + dep + "</a> ";
}

function createSearchResultsDom(arr) {
  let pkgsdom = "";
  for (const node of arr) {
    pkgsdom += createPkgButton(node.hiddenLabel)
  }
  return pkgsdom;
}

function createPkgListDom(list) {
  let depsdom = "";
  if (list == "")
    return "<i>Nothing</i>";
  for (let dep of list.split(", ")) {
    depsdom += createPkgButton(dep)
  }
  return depsdom;
}

var highlightActive = false;

function neighbourhoodHighlight(selectedNodes) {
    var nodesDataset = nodes;
    var edgesDataset = edges;
    var allNodes = nodedata;
    // if something is selected:
    if (selectedNodes.length > 0) {
      highlightActive = true;
      var i,j;
      var selectedNode = selectedNodes[0];
      var degrees = 2;

      // mark all nodes as hard to read.
      for (var nodeId in allNodes) {
        allNodes[nodeId].color = 'rgba(200,200,200,0.5)';
        if (allNodes[nodeId].label !== undefined) {
          allNodes[nodeId].label = undefined;
        }
      }
      var connectedNodes = network.getConnectedNodes(selectedNode);
      var allConnectedNodes = [];

      // get the second degree nodes
      for (i = 1; i < degrees; i++) {
        for (j = 0; j < connectedNodes.length; j++) {
          allConnectedNodes = allConnectedNodes.concat(network.getConnectedNodes(connectedNodes[j]));
        }
      }

      // all second degree nodes get a different color and their label back
      for (i = 0; i < allConnectedNodes.length; i++) {
        allNodes[allConnectedNodes[i]].color = 'rgba(150,150,150,0.75)';
        if (allNodes[allConnectedNodes[i]].label === undefined) {
          allNodes[allConnectedNodes[i]].label = allNodes[allConnectedNodes[i]].hiddenLabel;
        }
      }

      // all first degree nodes get their own color and their label back
      for (i = 0; i < connectedNodes.length; i++) {
        setNodeStyle(allNodes[connectedNodes[i]]);
        if (allNodes[connectedNodes[i]].label === undefined) {
          allNodes[connectedNodes[i]].label = allNodes[connectedNodes[i]].hiddenLabel;
        }
      }

      // the main node gets its own color and its label back.
      setNodeStyle(allNodes[selectedNode]);
      if (allNodes[selectedNode].label === undefined) {
        allNodes[selectedNode].label = allNodes[selectedNode].hiddenLabel;
      }
    }
    else if (highlightActive === true) {
      // reset all nodes
      for (var nodeId in allNodes) {
        allNodes[nodeId].color = undefined;
        if (allNodes[nodeId].label === undefined) {
          allNodes[nodeId].label = allNodes[nodeId].hiddenLabel;
        }
      }
      highlightActive = false
    }

    // transform the object into an array
    var updateArray = [];
    for (nodeId in allNodes) {
      if (allNodes.hasOwnProperty(nodeId)) {
        updateArray.push(allNodes[nodeId]);
      }
    }
    nodesDataset.update(updateArray);

  }

var deselectTimeout = null;

function selectPkg(node) {
  clearTimeout(deselectTimeout);
  document.getElementById("fsinfo").style.display = "block";
  document.querySelector('#fsinfo').className = "mdl-card mdl-shadow--4dp animated zoomIn";
  document.getElementById("pkgname").innerHTML = node.hiddenLabel;
  document.getElementById("pkgsizedesc").innerHTML = {"isize":"Installed", "csize":"Cascade", "cssize":"Recursive"}[currentsize] + " Size";
  document.getElementById("pkgsize").innerHTML = " - ";  // filesize(node[currentsize]);
  let reason = node.group == "normal" ? "as a dependency" : "explicitly";
  document.getElementById("pkgreason").innerHTML = reason;
  document.getElementById("pkgversion").innerHTML = node.version;
  document.getElementById("pkgdesc").innerHTML = node.desc;
  document.getElementById("pkglevel").innerHTML = node.level;
  document.getElementById("pkgrepo").innerHTML = node.repo;
  document.getElementById("pkgdeps").innerHTML = createPkgListDom(node.deps);
  document.getElementById("badgedep").setAttribute('data-badge', node.deps=="" ? 0 : node.deps.split(', ').length);
  document.getElementById("pkgreqs").innerHTML = createPkgListDom(node.reqs);
  document.getElementById("badgereq").setAttribute('data-badge', node.reqs=="" ? 0 : node.reqs.split(', ').length);
//  document.getElementById("pkggroups").innerHTML = createPkgListDom(node.groups);
//  document.getElementById("pkgprovides").innerHTML = node.provides;
}

function deselectPkg(){
  document.querySelector('#fsinfo').className = "mdl-card mdl-shadow--4dp animated zoomOut";
  deselectTimeout = setTimeout(function(){
    document.getElementById("fsinfo").style.display = "none";
  }, 300);

  // hide search content
  document.getElementById("search").value = "";
  document.getElementById("searchwrapper").className =
    document.getElementById("searchwrapper").className.replace(/\bis-dirty\b/,'');
  document.getElementById("searchwrapper").className =
    document.getElementById("searchwrapper").className.replace(/\bis-focused\b/,'');
}

function togglehide() {
  let pkgname = document.getElementById("pkgname").innerHTML;
  for (let node of nodes.get()) {
    if (node.hiddenLabel == pkgname) {
      var hide = !node.hidden;
      nodes.update({id : node.id, hidden : hide});
      for (let edge of edges.get()) {
        if (edge.from == node.id) {
          edges.update(
              {id : edge.id, hidden : hide || nodes.get()[edge.to].hidden});
        }
        if (edge.to == node.id) {
          edges.update(
              {id : edge.id, hidden : nodes.get()[edge.from].hidden || hide});
        }
      }
      selectPkg(node);
      network.stabilize(50);
    }
  }
}


function selectAndUnhidePkg(node){
    network.selectNodes([ node.id ]);
    selectPkg(node);
    if (!node.hidden) {
        network.focus(node.id, {
            scale : Math.log(nodes.length) / 5,
            locked : false,
            animation : {duration : 300}
        });
    }
    neighbourhoodHighlight([node.id]);
}

function trysearch() {
  let pkgname = document.getElementById("search").value;
  let found = false;
    if (!found) { // look for a close match 
	var pkgs = new Array(0)
	for (let node of nodes.get()) {
	    if (node.hiddenLabel.includes(pkgname)) {
		pkgs.push(node);
	    }
	}
	numPkgs = pkgs.length;
	if(numPkgs == 0) {
	    //  There are no matching packages
	    document.getElementById("searchresults").innerHTML = "<i>No matching packages</i>";"";
	}
	else if(numPkgs == 1) {
	    //  There is only one package so select it
	    selectAndUnhidePkg(pkgs[0]);
	    document.getElementById("searchresults").innerHTML = "";
	}
    	else if(numPkgs < 100 ){
	    // list all of the matching packages as clickable buttons
	    pkgs.sort()
	    document.getElementById("searchresults").innerHTML = createSearchResultsDom(pkgs);
	}
	else {
	    // there are too many packages so only display the count
	    document.getElementById("searchresults").innerHTML = "<i>" + numPkgs + " matching packages</i>";
	}
    }
}


function close_panel() {
  document.querySelector('#lefttoppanel').className = "lefttoppanel animated zoomOut";
  document.querySelector('#leftpanel_show').style.display = "block";
  document.querySelector('#leftpanel_show').className = "leftpanel-show mdl-button mdl-js-button mdl-button--fab mdl-js-ripple-effect animated zoomIn";
  setTimeout(function(){
    document.querySelector('#lefttoppanel').style.display = "none";
  }, 300);
}

function show_panel() {
  document.querySelector('#lefttoppanel').style.display = "flex";
  document.querySelector('#lefttoppanel').className = "lefttoppanel animated zoomIn";
  document.querySelector('#leftpanel_show').className = "leftpanel-show mdl-button mdl-js-button mdl-button--fab mdl-js-ripple-effect animated zoomOut";
}

function makeLegendGraph() {
  const nodes = [
    {
      id: 50,
      label: "world file package",
      level: 0,
      catagory: "explicit",
      build_status: "keep",
      stability: "overlay-live",
      x: 0
    },
    {
      id: 0,
      label: "gentoo::pkg arch",
      level: 2,
      catagory: "normal",
      build_status: "keep",
      stability: "stable"
    },
    {
      id: 1,
      label: "gentoo::pkg ~arch",
      level: 4,
      catagory: "normal",
      build_status: "keep",
      stability: "test"
    },
    {
      id: 2,
      label: "gentoo::pkg-9999",
      level: 6,
      catagory: "normal",
      build_status: "keep",
      stability: "live"
    },
    {
      id: 3,
      label: "overlay::pkg ~arch",
      level: 5,
      catagory: "normal",
      build_status: "keep",
      stability: "overlay-test",
      x: -100
    },
    {
      id: 4,
      label: "overlay::pkg-9999",
      level: 3,
      catagory: "normal",
      build_status: "keep",
      stability: "overlay-live",
      x: 1000
    },
    {
      id: 11,
      label: "package to be installed",
      level: 8,
      catagory: "normal",
      build_status: "add",
      stability: "stable",
      x: 30
    },
    {
      id: 12,
      label: "package to be removed",
      level: 0.5,
      catagory: "normal",
      build_status: "remove",
      stability: "stable",
      x: 30
    },
    {
      id: 13,
      label: "package to be rebuilt",
      level: 10,
      catagory: "normal",
      build_status: "rebuild",
      stability: "stable"
    },
    {
      id: 20,
      label: "dependency",
      level: 13,
      catagory: "normal",
      build_status: "keep",
      stability: "stable"
    },
    {
      id: 21,
      label: "virtual dependency",
      level: 8,
      catagory: "virtual",
      build_status: "keep",
      stability: "stable",
      x: -1
    },
    {
      id: 22,
      label: "@system dependency",
      level: 14,
      catagory: "system",
      build_status: "keep",
      stability: "stable",
    },
  ];
  const edges =  [
    { from: 50, to: 0},
    { from: 50, to: 1},
    { from: 50, to: 2},
    { from: 50, to: 3},
    { from: 50, to: 4},
    { from: 1, to: 20, label: "PDEPEND", dep: "PDEPEND"  },
    { from: 2, to: 20, label: "BDEPEND or DEPEND", dep: "DEPEND" },
    { from: 11, to: 22 },
    { from: 5, to: 22 },
    { from: 0, to: 21 },
    { from: 13, to: 22 },
    { from: 21, to: 20, label: "RDEPEND",dep: "RDEPEND" },
    { from: 12, to: 4 },
    { from: 4, to: 11 },
    { from: 3, to: 13 },
  ];

  for(let nodeid in nodes){
    let node = nodes[nodeid];
    node.scaling = { label: 
      {
        min: 15,
        drawThreshold: 1
      }
    };
    setNodeStyle(node);
  }

  for(let edgeid in edges) {
    let edge = edges[edgeid];
    edge.scaling = { label: 
      {
        min: 15,
        drawThreshold: 1
      }
    };
    setEdgeStyle(edge);
  }

  return {
      nodes: nodes,
      edges: edges
    };
}
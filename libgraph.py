import pygraphviz as pgv

def color(length):
  color = 'red'
  if length == 0:
    color = 'grey'
  if length == 1:
    color = 'black'
  if length == 2:
    color = 'blue'
  if length == 3:
    color = 'green'
  if length == 4:
    color = 'orange'
  return color

def generate_graph(nodes, fname, flink, ffontsize, layout_hint=None):
  G = pgv.AGraph()
  G.graph_attr.update(ranksep='0.5', size='500,500')
  G.node_attr.update(color='black', width='0.1', height='0.2', fontsize='8')
  G.edge_attr.update(arrowhead='normal', color="grey")
  if layout_hint:
    nodelist = layout_hint + nodes.keys()  # prepend starting points as a layout hint
  for n in nodelist:
    name = fname(n)
    c = color(len(nodes[n]))
    link = flink(n)
    fs = ffontsize(n)
    if G.has_node(name):
      N = G.get_node(fname(n))
      N.attr['color'] = c
      N.attr['URL'] = link
      N.attr['fontsize'] = fs
    else:
      G.add_node(name, color=c, URL=link, fontsize=fs)

    for e in nodes[n]:
      G.add_edge(name, fname(e))
  return G

def write_graph(G, filename):
  G.layout('dot')
  G.draw(filename)

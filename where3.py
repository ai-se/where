"""

# A Better Where

WHERE3 is a super-version of WHERE2, a near-linear time top-down clustering algorithm.

+ At each division, it keeps a summary of the data in a new _centroid_ variable.
+ Instead of dividing the data in half at each division, WHERE3
  splits in order to minimize the variance of the scores in each division. 



## Standard Header Stuff

"""
from __future__ import division,print_function
import  sys  
sys.dont_write_bytecode = True
from lib import *
import sdiv
from nasa93 import *

"""

## Dimensionality Reduction with Fastmp

Project data in N dimensions down to a single dimension connecting
twp distant points. Divide that data at the median of those projects.

"""
def fastmap(m,data):
  "Divide data into two using distance to two distant items."
  one  = any(data)             # 1) pick anything
  west = furthest(m,one,data)  # 2) west is as far as you can go from anything
  east = furthest(m,west,data) # 3) east is as far as you can go from west
  c    = dist(m,west,east)
  # now find everyone's distance
  lst = []
  for one in data:
    a = dist(m,one,west)
    b = dist(m,one,east)
    x = (a*a + c*c - b*b)/(2*c) # cosine rule
    y = max(0, a**2 - x**2)**0.5 
    if one.x0 is None: one.x0 = x # for displaying
    if one.y0 is None: one.y0 = y # for displaying
    lst  += [(x,one)]
  lst = sorted(lst)
  small  = 2*len(m._rows)**0.5
  splits = sdiv.divides(lst,
              tiny=small,
              num1=first,
              num2=lambda z: scores(m,second(z)))
  return west,east, c, [o(cut  = sp[0],
                          data = map(second,sp[1]),
                          sd   = sp[2]) 
                        for sp in splits]
"""

In the above:

+ _m_ is some model that generates candidate
  solutions that we wish to niche.
+ _(west,east)_ are not _the_ most distant points
  (that would require _N*N) distance
  calculations). But they are at least very distant
  to each other.

This code needs some helper functions. _Dist_ uses
the standard Euclidean measure. Note that you tune
what it uses to define the niches (decisions or
objectives) using the _what_ parameter:

"""
def dist(m,i,j,
         what = lambda m: m.decisions):
  "Euclidean distance 0 <= d <= 1 between decisions"
  n      = len(i.cells)
  deltas = 0
  for c in what(m):
    n1 = norm(m, c, i.cells[c])
    n2 = norm(m, c, j.cells[c])
    inc = (n1-n2)**2
    deltas += inc
    n += abs(m.w[c])
  return deltas**0.5 / n**0.5
"""

The _Dist_ function normalizes all the raw values zero to one.

"""
def norm(m,c,val) : 
  "Normalizes val in col c within model m 0..1"
  return (val- m.lo[c]) / (m.hi[c]- m.lo[c]+ 0.0001)
"""

Now we can define _furthest_:

"""
def furthest(m,i,all,
             init = 0,
             better = gt):
  "find which of all is furthest from 'i'"
  out,d= i,init
  for j in all:
    if i == j: continue
    tmp = dist(m,i,j)
    if better(tmp,d): 
      out,d = j,tmp
  return out
"""

And of course, _closest_:

"""
def closest(m,i,all):
  return furthest(m,i,all,init=10**32,better=lt)
"""

## WHERE2 = Recursive Fastmap


WHERE2 finds everyone's else's distance from the poles
  and divide the data on the mean point of those
  distances.  This all stops if:

+  Any division has _tooFew_ solutions (say,
  less than _sqrt_ of the total number of
  solutions).
+ Something has gone horribly wrong and you are
  recursing _tooDeep_

This code is controlled by the options in [_The_ settings](settingspy).  For
example, if _The.pruning_ is true, we may ignore
some sub-tree (this process is discussed, later on).
Also, if _The.verbose_ is true, the _show_
function prints out a little tree showing the
progress (and to print indents in that tree, we use
the string _The.b4_).  For example, here's WHERE2
dividing 93 examples from NASA93.
 
    ---| _where |-----------------
    93
    |.. 46
    |.. |.. 23
    |.. |.. |.. 11
    |.. |.. |.. |.. 5.
    |.. |.. |.. |.. 6.
    |.. |.. |.. 12
    |.. |.. |.. |.. 6.
    |.. |.. |.. |.. 6.
    |.. |.. 23
    |.. |.. |.. 11
    |.. |.. |.. |.. 5.
    |.. |.. |.. |.. 6.
    |.. |.. |.. 12
    |.. |.. |.. |.. 6.
    |.. |.. |.. |.. 6.
    |.. 47
    |.. |.. 23
    |.. |.. |.. 11
    |.. |.. |.. |.. 5.
    |.. |.. |.. |.. 6.
    |.. |.. |.. 12
    |.. |.. |.. |.. 6.
    |.. |.. |.. |.. 6.
    |.. |.. 24
    |.. |.. |.. 12
    |.. |.. |.. |.. 6.
    |.. |.. |.. |.. 6.
    |.. |.. |.. 12
    |.. |.. |.. |.. 6.
    |.. |.. |.. |.. 6.


WHERE2 returns clusters, where each cluster contains
multiple solutions.

"""
def where3(m, data, lvl=0, up=None, asIs = 10**32):
  node = o(val=None,_up=up,_kids=[], support=len(data),
           centroid= summary(data),sd = asIs)
  def tooDeep(): return lvl > The.depthMax
  def tooFew() : return len(data) < The.minSize
  def show(suffix): 
    if The.verbose: 
      print(The.b4*lvl,len(data),
            suffix,' ; ',id(node) % 1000,' :sd ',node.sd,sep='')
  if tooDeep() or tooFew():
    show(".")
    node.data = data
  else:
    show("")
    west,east, c, splits = fastmap(m,data)
    node.update(c=c,east=east,west=west)
    for split in splits:
      if len(split.data) < len(data):
        if split.sd*100 < asIs:
          node._kids += [o(cut=split.cut,
                           sub=where3(m, split.data,
                                 lvl=lvl+1,
                                 up=node,
                                 asIs = split.sd))]
  return node

def summary(rows):
  def med(*l): return median(l)
  rows = [x.cells for x in rows]
  return [med(*l) for l in zip(*rows)]
"""




### Model-specific Stuff

WHERE3 talks to models via the the following model-specific variables:

+ _m.cols_: list of indices in a list
+ _m.names_: a list of names for each column.
+ _m.decisions_: the subset of cols relating to decisions.
+ _m.obectives_: the subset of cols relating to objectives.
+ _m.eval(m,eg)_: function for computing variables from _eg_.
+ _m.lo[c]_ : the lowest value in column _c_.
+ _m.hi[c]_ : the highest value in column _c_.
+ _m.w[c]_: the weight for each column. Usually equal to one. 
  If an objective and if we are minimizing  that objective, then the weight is negative.


### Model-general stuff

Using the model-specific stuff, WHERE3 defines some
useful general functions.

"""
def some(m,x) :
  "with variable x of model m, pick one value at random" 
  return m.lo[x] + by(m.hi[x] - m.lo[x])

def scores(m,it):
  "Score an individual."
  if not it.scored:
    m.eval(m,it)
    new, w = 0, 0
    for c in m.objectives:
      val = it.cells[c]
      w  += abs(m.w[c])
      tmp = norm(m,c,val)
      if m.w[c] < 0: 
        tmp = 1 - tmp
      new += (tmp**2) 
    it.score = (new**0.5) / (w**0.5)
    it.scored = True
  return it.score
"""

## Tree Code

Tools for manipulating the tree returned by _where3_.

### Primitive: Walk the nodes

"""
def nodes(tree,seen=None,steps=0):
  if seen is None: seen=[]
  if tree:
   if not id(tree) in seen:
     seen.append(id(tree))
     yield tree,steps
     for kid in tree._kids:
       for sub,steps1 in nodes(kid.sub,seen,steps+1):
         yield sub,steps1
"""

### Return nodes that are leaves

"""
def leaves(tree,seen=None,steps=0):
  for node,steps1 in nodes(tree,seen,steps):
    if not node._kids:
      yield node,steps1

def leaf(m,one,node):
  if node._kids:
    a = dist(m,one,node.west)
    b = dist(m,one,node.east)
    c = node.c
    x = (a*a + c*c - b*b)/(2*c) 
    cut0 = -1 * 10**32
    #print(map(lambda x:x.cut,node._kids))
    lo = node._kids[0].cut
    hi = node._kids[-1].cut
    for kid in node._kids:
      cut = kid.cut
      if cut==lo and x <= cut: return leaf(m,one,kid.sub)
      if cut==hi and x >= cut: return leaf(m,one,kid.sub)
      if cut0 <= x < cut     : return leaf(m,one,kid.sub)
      cut0 = cut
  return node

"""

### Return nodes nearest to furthest

"""
def neighbors(leaf,seen=None,steps=-1):
  """Walk the tree from 'leaf' increasingly
     distant leaves. """
  if seen is None: seen=[]
  for down,steps1 in leaves(leaf,seen,steps+1):
    yield down,steps1
  if leaf:
    for up,steps1 in neighbors(leaf._up, seen,steps+1):
      yield up,steps1
"""

### Return nodes in Groups, Closest to Furthest


"""
def around(leaf, f=lambda x: x):
  tmp,last  = [], None
  for node,dist in neighbors(leaf):
    if dist > 0:
      if dist == last:
        tmp += [f(node)]
      else:
        if tmp:
          yield last,tmp
        tmp   = [f(node)]
    last = dist
  if tmp:
    yield last,tmp
"""
## Demo Code

### Code Showing the scores

"""
#@go
def _scores():
  m = nasa93()
  out = []
  for row in m._rows: 
    scores(m,row)
    out += [(row.score, [row.cells[c] for c in m.objectives])]
  for s,x in sorted(out):
    print(s,x)
"""

### Code Showing the Distances

"""
#@go
def _distances(m=nasa93):
   m=m()
   seed(The.seed)
   for i in m._rows:
     j = closest(m,i,  m._rows)
     k = furthest(m,i, m._rows)
     idec = [i.cells[c] for c in m.decisions]
     jdec = [j.cells[c] for c in m.decisions]
     kdec = [k.cells[c] for c in m.decisions]
     print("\n",
           gs(idec), g(scores(m,i)),"\n",
           gs(jdec),"closest ", g(dist(m,i,j)),"\n",
           gs(kdec),"furthest", g(dist(m,i,k)))
"""

### A Demo for  Where3.

"""
@go
def _where(m=nasa93):
  m= m()
  seed(1)
  told=N()
  for r in m._rows:
    s =  scores(m,r)
    told += s
  global The
  The=defaults(verbose = True,
               minSize = len(m._rows)**0.5,
               prune   = False,
               wriggle = 0.3*told.sd())
  tree = where3(m, m._rows) 
  n=0
  #for node,_ in leaves(tree):
  #  n += len(node.data)
  #  print(id(node) % 1000, ' ',end='')
  #  for near,dist in neighbors(node):
  #    print(dist,id(near) % 1000,' ',end='')
  #  print("")
  #print(n)
  filter = lambda z: id(z) % 1000
#  for node,_ in leaves(tree):
 #   print(filter(node), 
  #        [x for x in around(node,filter)])
  print("===================")
  for node1,_ in leaves(tree):
    for row in node1.data:
      node2  = leaf(m,row,tree)
      print(id(node1)%1000,id(node2)%1000)


"""
93 ; 648 :sd 100000000000000000000000000000000
|.. 5. ; 688 :sd 0.131721985241
|.. 13 ; 832 :sd 0.0502816234631
|.. |.. 6. ; 48 :sd 0.0495902279838
|.. |.. 7. ; 336 :sd 0.0436064936524
|.. 6. ; 480 :sd 0.253591931506
|.. 15 ; 768 :sd 0.0510130486783
|.. |.. 7. ; 416 :sd 0.0340741425218
|.. 9. ; 912 :sd 0.0676309885992
|.. 19 ; 776 :sd 0.0242475250614
|.. |.. 6. ; 112 :sd 0.0154888423331
|.. |.. 5. ; 400 :sd 0.0044788943576
|.. |.. 8. ; 688 :sd 0.00248546657439
|.. 5. ; 352 :sd 0.146791230857
|.. 9. ; 48 :sd 0.0112509526784
|.. 6. ; 336 :sd 0.101468090104
|.. 6. ; 624 :sd 0.0276130175275
"""

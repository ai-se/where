"""

# A Better Where

Updating old Where with new Python tricks.

## Standard Start stuf

"""
from __future__ import division,print_function
import  sys
sys.dont_write_bytecode = True
from lib import *
from nasa93 import *

def fastmap(m,data):
  "Divide data into two using distance to two distant items."
  one  = any(data)             # 1) pick anything
  west = furthest(m,one,data)  # 2) west is as far as you can go from anything
  east = furthest(m,west,data) # 3) east is as far as you can go from west
  c    = dist(m,west,east)
  # now find everyone's distance
  xsum, lst = 0.0,[]
  for one in data:
    a = dist(m,one,west)
    b = dist(m,one,east)
    x = (a*a + c*c - b*b)/(2*c) # cosine rule
    xsum += x
    lst  += [(x,one)]
  # now cut data according to the mean distance
  cut, wests, easts = xsum/len(data), [], []
  for x,one in lst:
    where = wests if x < cut else easts 
    where += [one]
  return wests,west, easts,east
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
         what = lambda x: x.dec):
  "Euclidean distance 0 <= d <= 1 between decisions"
  d1,d2  = what(i), what(j)
  n      = len(d1)
  deltas = 0
  for d in range(n):
    n1 = norm(m, d, d1[d])
    n2 = norm(m, d, d2[d])
    inc = (n1-n2)**2
    deltas += inc
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
             better = lambda x,y: x>y):
  "find which of all is furthest from 'i'"
  out,d= i,init
  for j in all:
    if not i == j:
      tmp = dist(m,i,j)
      if better(tmp,d): out,d = j,tmp
  return out
"""

WHERE finds everyone's else's distance from the poles
  and divide the data on the mean point of those
  distances.  This all stops if:

+  Any division has _tooFew_ solutions (say,
  less than _sqrt_ of the total number of
  solutions).
+ Something has gone horribly wrong and you are
  recursing _tooDeep_

This code is controlled by a set of _slots_.  For
example, if _slots.pruning_ is true, we may ignore
some sub-tree (this process is discussed, later on).
Also, if _slots.verbose_ is true, the _show_
function prints out a little tree showing the
progress (and to print indents in that tree, we use
the string _slots.b4_).  For example, here's WHERE
dividing 100 solutions:
    
    100
    |.. 50
    |.. |.. 25
    |.. |.. |.. 11
    |.. |.. |.. |.. 6.
    |.. |.. |.. |.. 5.
    |.. |.. |.. 14
    |.. |.. |.. |.. 6.
    |.. |.. |.. |.. 8.
    |.. |.. 25
    |.. |.. |.. 12
    |.. |.. |.. |.. 5.
    |.. |.. |.. |.. 7.
    |.. |.. |.. 13
    |.. |.. |.. |.. 5.
    |.. |.. |.. |.. 8.
    |.. 50
    |.. |.. 25
    |.. |.. |.. 13
    |.. |.. |.. |.. 7.
    |.. |.. |.. |.. 6.
    |.. |.. |.. 12
    |.. |.. |.. |.. 5.
    |.. |.. |.. |.. 7.
    |.. |.. 25
    |.. |.. |.. 11
    |.. |.. |.. |.. 5.
    |.. |.. |.. |.. 6.
    |.. |.. |.. 14
    |.. |.. |.. |.. 7.
    |.. |.. |.. |.. 7.

Here's the slots:

""" 

"""

WHERE returns clusters, where each cluster contains
multiple solutions.

"""
def where0(**other):
  return o(minSize  = 10,    # min leaf size
               depthMin= 2,      # no pruning till this depth
               depthMax= 10,     # max tree depth
               wriggle = 0.2,    # min difference of 'better'
               prune   = True,   # pruning enabled?
               b4      = '|.. ', # indent string
               verbose = False,  # show trace info?
               hedges  = 0.38    # strict=0.38,relax=0.17
   ).update(**other)

def where(m,data,slots=where0()):
  out = []
  where1(m,data,slots,0,out)
  return out

def where1(m, data, slots, lvl, out):
  def tooDeep(): return lvl > slots.depthMax
  def tooFew() : return len(data) < slots.minSize
  def show(suffix): 
    if slots.verbose: 
      print(slots.b4*lvl,len(data),suffix,sep='')
  if tooDeep() or tooFew():
    show(".")
    out += [data]
  else:
    show("")
    wests,west, easts,east = fastmap(m,data)
    goLeft, goRight = maybePrune(m,slots,lvl,west,east)
    if goLeft: 
      where1(m, wests, slots, lvl+1, out)
    if goRight: 
      where1(m, easts, slots, lvl+1, out)
"""

Is this useful? Well, in the following experiment, I
clustered 32, 64, 128, 256 individuals using WHERE or
a dumb greedy approach called GAC that (a) finds
everyone's closest neighbor; (b) combines each such
pair into a super-node; (c) then repeats
(recursively) for the super-nodes.

[[etc/img/gacWHEREruntimes.png]]




WHERE is _much_ faster than GAC since it builds
a tree of cluster of height log(N) by, at each
step, making only  O(2N) calls to FastMap.

### Experimental Extensions

Lately I've been experimenting with a system that
prunes as it divides the data. GALE checks for
domination between the poles and ignores data in
halves with a dominated pole. This means that for
_N_ solutions we only ever have to evaluate
_2*log(N)_ of them- which is useful if each
evaluation takes a long time.  

The niches found in this way
contain non-dominated poles; i.e. they are
approximations to the Pareto frontier.
Preliminary results show that this is a useful
approach but you should treat those results with a
grain of salt.

In any case, this code supports that pruning as an
optional extra (and is enabled using the
_slots.pruning_ flag). In summary, this code says if
the scores for the poles are more different that
_slots.wriggle_ and one pole has a better score than
the other, then ignore the other pole.

"""
def maybePrune(m,slots,lvl,west,east):
  "Usually, go left then right, unless dominated."
  goLeft, goRight = True,True # default
  if  slots.prune and lvl >= slots.depthMin:
    sw = scores(m, west)
    se = scores(m, east)
    if abs(sw - se) > slots.wriggle: # big enough to consider
      if se > sw: goLeft   = False   # no left
      if sw > se: goRight  = False   # no right
  return goLeft, goRight
"""

Note that I do not allow pruning until we have
descended at least _slots.depthMin_ into the tree.

### Model-specific Stuff

WHERE talks to models via the the following model-specific functions.
Here, we must invent some made-up model that builds
individuals with 4 decisions and 3 objectives.
In practice, you would **start** here to build hooks from WHERE into your model
(which is the **m** passed in to these functions).

"""


"""

The call to 
### Model-general stuff

Using the model-specific stuff, WHERE defines some
useful general functions.

"""
def some(m,x) :
  "with variable x of model m, pick one value at random" 
  return m.lo[x] + by(m.hi[x] - m.lo[x])

def candidate(m):
  "Return an individual."
  for row in m._rows:
    yield row

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
    it.scores = (new**0.5) / (w**0.5)
    it.scored = True
  return it.scores

#@go
def _scores():
  m = nasa93()
  for row in m._rows: 
    scores(m,row)
    print([row.cells[c] for c in m.objectives],row.scores)

"""


### Demo stuff

To run these at load time, add _@go_ (uncommented) on the line before.

Checks that we can find lost and distant things:

"""
@go
def _distances():
  def closest(m,i,all):
    return furthest(m,i,all,10**32,lambda x,y: x < y)
  random.seed(1)
  m   = "any"
  pop = [candidate(m) for _ in range(4)]  
  for i in pop:
    j = closest(m,i,pop)
    k = furthest(m,i,pop)
    print("\n",
          gs(i.dec), g(scores(m,i)),"\n",
          gs(j.dec),"closest ", g(dist(m,i,j)),"\n",
          gs(k.dec),"furthest", g(dist(m,i,k)))
    print(i)
"""

A standard call to WHERE, pruning disabled:

"""
@go
def _where():
  random.seed(1)
  m, max, pop, kept = "model",100, [], N()
  for _ in range(max):
    one = candidate(m)
    kept + scores(m,one)
    pop += [one]
  slots = where0(verbose = True,
               minSize = max**0.5,
               prune   = False,
               wriggle = 0.3*kept.s())
  n=0
  for leaf in where(m, pop, slots):
    n += len(leaf)
  print(n,slots)
"""

Compares WHERE to GAC:

"""
#@go
def _whereTiming():
  def allPairs(data):
    n = 8.0/3*(len(data)**2 - 1) #numevals WHERE vs GAC
    for _ in range(int(n+0.5)):
      d1 = any(data)
      d2 = any(data)
      dist("M",d1,d2)
  random.seed(1)
  for max in [32,64,128,256]:
    m, pop, kept = "model",[], N()
    for _ in range(max):
      one = candidate(m)
      kept + scores(m,one)
      pop += [one]
    slots = where0(verbose = False,
                minSize = 2, # emulate GAC
                depthMax=1000000,
                prune   = False,
                wriggle = 0.3*kept.s())
    t1 =  timing(lambda : where(m, pop, slots),10)
    t2 =  timing(lambda : allPairs(pop),10)
    print(max,t1,t2, int(100*t2/t1))

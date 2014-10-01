"""

# A Better Where

WHAT uses an adaption of the WHERE2 strategy to implement a supervised
near-linear time top-down clustering algorithm.

+ At each division, it keeps a summary of the data in a new _centroid_ variable.
+ Instead of dividing the data in half at each division, WHAT
  splits in order to minimize the variance of the scores in each division. 



## Standard Header Stuff

"""
from __future__ import division,print_function
import  sys,random,math
sys.dont_write_bytecode = True
import sdiv
from nasa93 import *

"""

# Support Code


# Place to store settings.

## Usual Header


## Anonymous Containers

"""
class o:
  def __init__(i,**d): i.has().update(**d)
  def has(i): return i.__dict__
  def update(i,**d) : i.has().update(d); return i
  def __repr__(i)   : 
    show=[':%s %s' % (k,i.has()[k]) 
      for k in sorted(i.has().keys() ) 
      if k[0] is not "_"]
    txt = ' '.join(show)
    if len(txt) > 60:
      show=map(lambda x: '\t'+x+'\n',show)
    return '{'+' '.join(show)+'}'

def defaults(**d):
  return o(_logo="""
                      <>
        .-"-"-.       ||______________________
       /=      \      ||-._`-._ :| |: _.-'_.-|
      |- /~~~\  |     ||   `-._`:| |:`_.-'   |
      |=( '.' ) |     ||-------`-' '-'-------|
      \__\_=_/__/     ||------_.-. .-._------|
       {_______}      ||  _.-'_.:| |:._`-._  |
     /` *       `'--._||-'_.-'  :| |:  `-._`-|
    /= .     [] .     { >~~~~~~~~~~~~~~~~~~~~~
   /  /|ooo     |`'--'||
  (   )\_______/      ||
   \``\/       \      ||
    `-| ==    \_|     ||
      /         |     ||
     |=   >\  __/     ||
     \   \ |- --|     ||
      \ __| \___/     ||
 jgs  _{__} _{__}     ||
     (    )(    )     ||
 ^^~  `"-"  `"-"  ~^^^~^^~~~^^^~^^^~^^^~^^~^ """,
      what=o(minSize  = 4,    # min leaf size
             depthMin= 2,      # no pruning till this depth
             depthMax= 10,     # max tree depth
             wriggle = 0.2,    # min difference of 'better'
             prune   = True,   # pruning enabled?
             b4      = '|.. ', # indent string
             verbose = False,  # show trace info?
             goal    = lambda m,x : scores(m,x)
             ),
      seed    = 1,
      cache   = o(size=128)
  ).update(**d)


"""

## Simple, low-level stuff

"""
def oneTwo(lst):
  one = lst[0]
  for two in lst[1:]:
    yield one,two
    one = two
"""
### Maths Stuff

"""
def gt(x,y): return x > y
def lt(x,y): return x < y

def medianIQR(lst, ordered=False):
  if not ordered: 
    lst = sorted(lst)
  n = len(lst)
  q = n//4
  iqr = lst[q*3] - lst[q]
  if n % 2: 
    return lst[q*2],iqr
  else:
    p = max(0,q-1)
    return (lst[p] + lst[q]) * 0.5,iqr

def median(lst,ordered=False):
  return medianIQR(lst,ordered)[0]



"""

An accumulator for reporting on numbers.

"""
class N(): 
  "Add/delete counts of numbers."
  def __init__(i,inits=[]):
    i.zero()
    map(i.__iadd__,inits)
  def zero(i): 
    i.n = i.mu = i.m2 = 0
    i.cache= Cache()
  def sd(i)  : 
    if i.n < 2: 
      return 0
    else:       
      return (max(0,i.m2)/(i.n - 1))**0.5
  def __iadd__(i,x):
    i.cache += x
    i.n     += 1
    delta    = x - i.mu
    i.mu    += delta/(1.0*i.n)
    i.m2    += delta*(x - i.mu)
    return i
  def __isub__(i,x):
    i.cache = Cache()
    if i.n < 2: return i.zero()
    i.n  -= 1
    delta = x - i.mu
    i.mu -= delta/(1.0*i.n)
    i.m2 -= delta*(x - i.mu)  
    return i

class Cache:
  "Keep a random sample of stuff seen so far."
  def __init__(i,inits=[]):
    i.all,i.n,i._has = [],0,None
    map(i.__iadd__,inits)
  def __iadd__(i,x):
    i.n += 1
    if len(i.all) < The.cache.size: # if not full
      i._has = None
      i.all += [x]               # then add
    else: # otherwise, maybe replace an old item
      if random.random() <= The.cache.size/i.n:
        i._has=None
        i.all[int(random.random()*The.cache.size)] = x
    return i
  def has(i):
    if i._has == None:
      lst  = sorted(i.all)
      med,iqr = medianIQR(i.all,ordered=True)
      i._has = o(
        median = med,      iqr = iqr,
        lo     = i.all[0], hi  = i.all[-1])
    return i._has
"""

### Random stuff.

"""
by   = lambda x: random.uniform(0,x) 
rseed = random.seed
any  = random.choice
rand = random.random

def seed(r=None):
  global The
  if The is None: The=defaults()
  if r is None: r = The.seed
  rseed(r)

"""

### List Handling Tricks

"""
def first(lst): return lst[0]
def second(lst): return lst[1]
def third(lst): return lst[2]
"""

### Printing Stuff

Print without newline:

"""
def say(*lst): print(*lst,end="")
"""

Print a list of numbers without an excess of decimal places:

"""
def gs(lst) : return [g(x) for x in lst]
def g(x)    : 
  txt = '%g' % x
  return int(txt) if int(x) == x else float(txt)
"""

Pretty print a dictionary:

"""
def showd(d):
  def one(k,v):
    if isinstance(v,list):
      v = gs(v)
    if isinstance(v,float):
      return ":%s %g" % (k,v)
    return ":%s %s" % (k,v)
  return ' '.join([one(k,v) for k,v in
                    sorted(d.items())
                     if not "_" in k])
"""

## Decorator to run code at Start-up

"""
def go(f):
  "A decorator that runs code at load time."
  print("\n# ---|", f.__name__,"|-----------------")
  if f.__doc__: print("#", f.__doc__)
  f()
"""

## Handling command line options.

Convert command line to a function call.
e.g. if the file lib.py ends with

    if __name__ == '__main__':eval(todo())

then 

    python lib.py myfun :a 1 :b fred  

results in a call to  _myfun(a=1,b='fred')_.

"""
def todo(com="print(The._logo,'WHERE (2.0) you at?')"):
  import sys
  if len(sys.argv) < 2: return com
  def strp(x): return isinstance(x,basestring)
  def wrap(x): return "'%s'"%x if strp(x) else str(x)  
  def oneTwo(lst):
    while lst: yield lst.pop(0), lst.pop(0)
  def value(x):
    try:    return eval(x)
    except: return x
  def two(x,y): return x[1:] +"="+wrap(value(y))
  twos = [two(x,y) for x,y in oneTwo(sys.argv[2:])]
  return sys.argv[1]+'(**dict('+ ','.join(twos)+'))'
"""

## More interesting, low-level stuff

"""
def timing(f,repeats=10):
  "How long does 'f' take to run?"
  import time
  time1 = time.clock()
  for _ in range(repeats):
    f()
  return (time.clock() - time1)*1.0/repeats
"""

## Data Completion Tool

Fills in some details on a table of data. For example, 

     def nasa93():
       vl=1;l=2;n=3;h=4;vh=5;xh=6
       return data(indep= [ 
                     'Prec', 'Flex', 'Resl', 'Team', 'Pmat', 'rely', 'data', 'cplx', 'ruse',
                     'docu', 'time', 'stor', 'pvol', 'acap', 'pcap', 'pcon', 'aexp', 'plex',  
                     'ltex', 'tool', 'site', 'sced', 'kloc'],
                   less = ['effort', 'defects', 'months'],
                   _rows=[
                      [h,h,h,vh,h,h,l,h,n,n,n,n,l,n,n,n,n,n,h,n,n,l,25.9,117.6,808,15.3],
                      [h,h,h,vh,h,h,l,h,n,n,n,n,l,n,n,n,n,n,h,n,n,l,24.6,117.6,767,15.0],
                      [h,h,h,vh,h,h,l,h,n,n,n,n,l,n,n,n,n,n,h,n,n,l,7.7,31.2,240,10.1],
     ...

Adds in information on _cols_, _decisions_, _hi,lo_, etc:

    {	:cols [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 
             12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 
             22, 22, 23, 24]
 	    :decisions [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 
                  11, 12, 13, 14, 15, 16, 17, 18, 
                  19, 20, 21, 22]
 	    :eval <function <lambda> at 0x7f3f825bea28>
 	    :hi {0: 4, 1: 4, 2: 4, 3: 5, 4: 4, 5: 5, 6: 5, 
           7: 6, 8: 3, 9: 3, 10: 6, 11: 6, 12: 4, 13: 5, 
           14: 5, 15: 3, 16: 5, 17: 4, 18: 4, 19: 4, 
           20: 3, 21: 3, 22: 980, 23: 8211, 24: 50961}
 	    :lo {0: 4, 1: 4, 2: 4, 3: 5, 4: 2, 5: 2, 6: 2, 
           7: 2, 8: 3, 9: 3, 10: 3, 11: 3, 12: 2, 
           13: 3, 14: 3, 15: 3, 16: 2, 17: 1, 18: 1, 
            19: 3, 20: 3, 21: 2, 22: 0.9, 23: 8.4, 24: 28}
 	    :names ['Prec', 'Flex', 'Resl', 'Team', 'Pmat', 
              'rely', 'data', 'cplx', 'ruse', 'docu', 
              'time', 'stor', 'pvol', 'acap', 'pcap', 
              'pcon', 'aexp', 'plex', 'ltex', 'tool', 
              'site', 'sced', 'kloc', 'effort', 
              'defects', 'months']
 	    :objectives [22, 23, 24]
 	    :w {0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 
          7: 1, 8: 1, 9: 1, 10: 1, 11: 1, 12: 1, 13: 1, 
          14: 1, 15: 1, 16: 1, 17: 1, 18: 1, 19: 1, 
          20: 1, 21: 1, 22: -1, 23: -1, 24: -1}
    }

Code:

"""
def data(indep=[], less=[], more=[], _rows=[]):
  nindep= len(indep)
  ndep  = len(less) + len(more)
  m= o(lo={}, hi={}, w={}, 
       eval  = lambda m,it : True,
       _rows = [o(cells=r,score=0,scored=False,
                  x0=None,y0=None) 
                for r in _rows],
       names = indep+less+more)
  m.decisions  = [x for x in range(nindep)]
  m.objectives = [nindep+ x- 1 for x in range(ndep)]
  m.cols       = m.decisions + m.objectives
  for x in m.decisions : 
    m.w[x]=  1
  for y,_ in enumerate(less) : 
    m.w[x+y]   = -1
  for z,_ in enumerate(more) : 
    m.w[x+y+z] =  1
  for x in m.cols:
    all = sorted(row.cells[x] for row in m._rows)
    m.lo[x] = all[0]
    m.hi[x] = all[-1]
  return m
"""

## Start-up Actions



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
  splits = sdiv.divides(lst,
              tiny= 2*len(m._rows)**0.5,
              num1= first,
              num2= lambda z: scores(m,second(z)))
  return west,east, c, spreadOut(splits,f=second)

def spreadOut(lst, f=lambda z:z):
  def oneTwo(lst):
    one = lst[0]
    for two in lst[1:]:
      yield one,two
      one = two
  out = [o(lo= cut1, hi= cut2, sd= sd1,
           data = map(f,data1))
         for (cut1,data1,sd1), (cut2,_,_) 
         in oneTwo(lst)]
  cut,data,sd = lst[-1]
  out += [o(lo=cut,hi=10**32,
            data = map(f,data), sd=sd)]
  out[0].lo = -10**32
  return out
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

### Model-specific Stuff

WHAT talks to models via the the following model-specific variables:

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

Using the model-specific stuff, WHAT defines some
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
def what(m,data):                                      
  score = lambda x: The.what.goal(m,x)
  all   = N(map(score, data))
  return what1(m,data, sd=all.sd()) 
  
def what1(m, data, lvl=0, up=None, sd=None):
  print(o(v=The.what.verbose,min=The.what.minSize,
          lvl=lvl,max=The.what.depthMax,n=len(data)))
  node = o(val=None,_up=up,_kids=[], support=len(data),
           centroid= summary(data),sd=sd)
  def tooDeep(): return lvl > The.what.depthMax
  def tooFew() : return len(data) < The.what.minSize
  def show(suffix): 
    if The.what.verbose: 
      print(The.what.b4*lvl,len(data),
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
        if lvl >= The.what.depthMin and split.sd*100 < sd:
          node._kids += [o(cut = (split.lo, split.hi),
                           sub = what1(m, split.data,
                                       lvl= lvl+1,
                                       up = node,
                                       sd = split.sd))]
  return node

def summary(rows):
  def med(*l): return median(l)
  rows = [x.cells for x in rows]
  return [med(*l) for l in zip(*rows)]
"""





## Tree Code

Tools for manipulating the tree returned by _what_.

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
def _distances(m=None):
   if m == None:  m = nasa93
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

### A Demo for  What.

"""
The=defaults()

@go
def _what(m=nasa93):
  m= m()
  seed(1)
  told=N()
  for r in m._rows:
    s =  scores(m,r)
    told += s
  global The
  print("L>",0.5*len(m._rows)**0.5)
  The.what.update(verbose = True,
               minSize = 0.5*len(m._rows)**0.5,
               prune   = False,
               wriggle = 0.3*told.sd())
  tree = what(m, m._rows) 
  exit()
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
  exit()
  for node1,_ in leaves(tree):
    for row in node1.data:
      node2  = leaf(m,row,tree)
      print(id(node1)%1000,id(node2)%1000)

#_what()

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

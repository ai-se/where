"""
fast simulated annealing
"""

from __future__ import division,print_function
import  sys,random,math,collections
sys.dont_write_bytecode = True

rseed = random.seed
any   = random.choice

class o:
  id=0
  def __init__(i, **d): 
    i.id = o.id = o.id + 1
    i.has().update(**d)
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

def items(x):
  if isinstance(x,list):
    for y in x:
      for z in items(y):  
        yield z
  elif isinstance(x,dict):
    for y in x.values():
      for z in items(y): 
        yield z
  else: 
    yield x

class S:
  def __init__(i,pos=0):
    i.pos,i.n,i.most,i.mode,i.w = pos, 0, 0, None, 1
    i.counts = collections.defaultdict(lambda : 0)
  def diff(i,x,y):
    return 0 if x == y else 1
  def near(i,x,y,z,f=0.3):
    w = y if rand() < f else z
    return x if w == x else w
  def __iadd__(i,x):
    assert not isinstance(x,(float,int))
    i.n += 1
    c = i.counts[x] = i.counts[x] + 1
    if c > i.most:
      i.mode, i.most = x, i.n
    return i

def _s():
  rseed(1)
  l = list('abcdefhhijklmnopqrstuvwxyz')
  s = S()
  for _ in xrange(1000): s += any(l)
  print(s.counts,s.mode,s.most)

class N:
  def __init__(i,pos=0):
    i.pos,i.lo,i.hi,i.w = pos, 10**32, -1*10**32, 1
  def near(i,x,y,z,f=0.3):
    return x + f*(y-z)
  def diff(i,x,y):
    x = (x - i.lo)/(i.hi - i.lo + 0.00001)
    y = (y - i.lo)/(i.hi - i.lo + 0.00001)
    return (x-y)**2
  def __iadd__(i,x):
    assert isinstance(x,(float,int))
    i.lo = min(i.lo,x)
    i.hi = max(i.hi,x)
    return i

def _n():
  rseed(1)
  l = range(0,23)
  n = N()
  for _ in xrange(10): n += any(l)
  print(n.lo,n.hi)

class G:
  def __init__(i,cells1,cells2,width=12):
    i.width, i.cols,i._tiles,i.xys = width, [], None,None
    row1, row2 = Row(i,cells1), Row(i,cells2)
    i.tell(row1);  i.tell(row2)
    i.poles(row1,row2)
    i.place(row1); i.place(row2)
  def tiles(i):
    i._tiles = i._tiles or [
               [{} for _ in range(i.width)] 
               for j in range(i.width)]
    return i._tiles
  def poles(west,east):
    i.west,i.east,i._tiles,i.xys = west,east,None,{}
  def tell(i,row):
    def ns(x,n): 
      return N if isinstance(x,(float,int)) else S
    def cols0():
      return [ns(x)(n) for 
              n,x in enumerate(row.cells)]
    i.cols = i.cols or cols0() 
    for cell,col in zip(row.cells,i.cols): 
      col += cell
  def place(i,row):
    x,y = row.xy()
    x = int(round(x * i.width))
    y = int(round(y * i.width))
    i.tiles()[x][y][row.id] = row
  def __iadd__(i, cells):
    row = Row(i,cells)
    i.tell(row)
    a = row - i.west
    b = row - i.east
    if a > c: 
      if not b > c:
        i.poles(row,i.east)
    if b > c: 
      i.poles(i.west,row)
    return i

class Row:
  id = 0
  def __init__(i,g,cells=[]):
    i.id = Row.id = Row.id + 1
    i.g, i.cells, i.x, i.y = g, cells, None, None
  def xy(i):
    cache = i.xys()
    key   = i.id
    if not key in cache: 
      cache[key] = i.xy0()
    return cache[key]
  def xy0(i):
    a = i - i.west
    b = i - i.east
    c = i.g.c
    x = (a*a + c*c - b*b)/(2*c + 0.0001) 
    y = max(0, a**2 - x**2)**0.5 
    return x,y
  def __sub__(i,j):
    ds = ws = 0
    for x,y,col in zip(i.cells, j.cells,  g.cols):
      ds += col.diff(x,y)
      ws += col.w
    return ds**0.5 / ws**0.5


"""
@include "lib.awk"
@include "genicLib.awk"

function _genic(      _Genic,o) {
  if (args("-d,data/weather.csv,--dump,0"\
           ",-k,10,-m,20,-n,100,-s,1",o)) {
    k = o["-k"]
    m = o["-m"]
    n = o["-n"]
    print "!!",FS,OFS
    srand(o["-s"])
    genic("cat " o["-d"], _Genic) }
}
function genic(com, _Genic,    rows) {
  a(centroid) a(age)
  while((com | getline)  > 0) { 
    gsub(/([ \t\r])|#.*)/,"")
    if($0)  {
      if (length(centroid) < k) 
	more(_Genic)
      else {
	 genic1(rows++,_Genic)
	 if (rows % n == 0) less(_Genic)
}}}}
function genic1(rows,_Genic,   i,this,row) {
  say("=")
  for(i=1;i<=NF;i++) {
    row[i] = $i
    rows==0 ? head(i,$i,_Genic) : lohi(i,$i,_Genic)
  }
  this = nearest(row,_Genic)
  move(++weight[this],centroid[this],row)
}
function more(_Genic,   i,new) {
  say("+")
  new = gensym("center")
  weight[new] = age[new] = 0 
  for(i=1;i<=NF;i++) 
    centroid[new][i]=$i
}
function less(_Genic,   sum,c,die) { 
  for(c in centroid) {
    sum    += weight[c]
    age[c] += centroid[c]
  }
  for(c in centroid) if (weight[c]/sum < rand()) die[c]
  for(c in die) {
    delete centroid[c]
    delete age[c]
  }
  delete weight
}
function move(w,olds,news,_Genic,   old,new,pos) {
  for(pos in name) { 
    if (pos in goalp) continue
    new = news[pos]
    old = olds[pos]
    if (new == avoid) { continue }
    if (old == avoid) { olds[pos] = new; continue }
    if (pos in nump)
      olds[pos] = (old*w + new)/(w + 1)
    else
      olds[pos] = (rand() < 1/w ? old : new)
}}
"""

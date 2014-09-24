"""

# Support Code


## Dull, low-level stuff

"""
from __future__ import division,print_function
import  sys,random,math
sys.dont_write_bytecode = True

class o:
  def __init__(i,**d): i.update(**d)
  def update(i,**d) : i.__dict__.update(d); return i
  def __repr__(i):
    show= ['\t:%s %s\n' % (k,i.__dict__[k]) 
           for k in sorted(i.__dict__.keys() )
           if k[0] is not "_"]
    return '{'+' '.join(show)+'}'



def todo(com="print('Your wish is my command.')"):
  """
  Convert command line to a function call.
  e.g. python lib.py myfun :a 1 :b fred
  calls myfun(a=1,b='fred')
  """
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

def _cmdDemo(a=1,b=2):
  print(b)

def go(f):
  "A decorator that runs code at load time."
  print("\n# ---|", f.__name__,"|-----------------")
  if f.__doc__: print("#", f.__doc__)
  f()
"""

Random stuff.

"""
by   = lambda x: random.uniform(0,x) 
seed = random.seed
any  = random.choice
"""

Pretty-prints for list

"""
def gs(lst) : return [g(x) for x in lst]
def g(x)    : return float('%g' % x) 
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

def showd(d):
  "Pretty print a dictionary."
  def one(k,v):
    if isinstance(v,list):
      v = gs(v)
    if isinstance(v,float):
      return ":%s %g" % (k,v)
    return ":%s %s" % (k,v)
  return ' '.join([one(k,v) for k,v in
                    sorted(d.items())
                     if not "_" in k])

class N:
  "An Accumulator for numbers"
  def __init__(i): i.n = i.m2 = i.mu = 0.0
  def s(i)       : return (i.m2/(i.n - 1))**0.5
  def __iadd__(i,x):
    i.n   += 1    
    delta  = x - i.mu
    i.mu  += delta*1.0/i.n
    i.m2  += delta*(x - i.mu)
    return i

def data(indep=[], less=[], more=[], _rows=[]):
  nindep= len(indep)
  ndep  = len(less) + len(more)
  m= o(lo={}, hi={}, w={}, 
       eval  = lambda m,it : m,
       _rows = [o(cells=r,score=0,scored=False) 
                for r in _rows],
       names = indep+less+more)
  m.decisions  = [x for x in range(nindep)]
  m.objectives = [nindep+ x- 1 for x in range(ndep)]
  for x in m.decisions : 
    m.w[x]=  1
  for y,_ in enumerate(less) : 
    m.w[x+y]   = -1
  for z,_ in enumerate(more) : 
    m.w[x+y+z] =  1
  for x in m.decisions:
    all = sorted(row.cells[x] for row in m._rows)
    m.lo[x] = all[0]
    m.hi[x] = all[-1]
  for x in m.objectives:
    all = sorted(row.cells[x] for row in m._rows)
    m.lo[x] = all[0]
    m.hi[x] = all[-1]
  return m

if __name__ == '__main__': eval(todo())

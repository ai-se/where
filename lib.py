"""

Support Code
------------

### Dull, low-level stuff

"""

from __future__ import division,print_function
import  sys,random
sys.dont_write_bytecode = True

def go(f):
  "A decorator that runs code at load time."
  print("\n# ---|", f.__name__,"|-----------------")
  if f.__doc__: print("#", f.__doc__)
  f()

# random stuff
by   = lambda x: random.uniform(0,x) 
seed = random.seed
any  = random.choice

# pretty-prints for list
def gs(lst) : return [g(x) for x in lst]
def g(x)    : return float('%g' % x) 

"""

### More interesting, low-level stuff

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

class Num:
  "An Accumulator for numbers"
  def __init__(i): i.n = i.m2 = i.mu = 0.0
  def s(i)       : return (i.m2/(i.n - 1))**0.5
  def __add__(i,x):
    i.n   += 1    
    delta  = x - i.mu
    i.mu  += delta*1.0/i.n
    i.m2  += delta*(x - i.mu)

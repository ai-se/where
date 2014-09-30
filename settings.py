"""

# Place to store settings.

## Usual Header

"""
import  sys
sys.dont_write_bytecode = True
"""

## Anonymous Containers

"""
class o:
  def __init__(i,**d): i.has().update(**d)
  def has(i): return i.__dict__
  def update(i,**d) : i.has().update(d); return i
  def __repr__(i)   : 
    show=['\t:%s %s\n' % (k,i.has()[k]) 
      for k in sorted(i.has().keys() ) 
      if k[0] is not "_"]
    return '{'+' '.join(show)+'}'
"""

## Defining the defaults

"""

def the(what,**d):
  global The
  if  what in The.has(): 
    print('Options name class: that name [%s] is taken.' % what)
    exit()
  The.has()[what] = o(**d)
  
def defaults(**also):
  return o(_logo="""
            ,.-""``""-.,
           /  ,:,;;,;,  \ 
           \  ';';;';'  /
            `'---;;---'`
            <>_==""==_<>
            _<<<<<>>>>>_
          .'____\==/____'.
          |__   |__|   __|
         /C  \  |..|  /  D\ 
         \_C_/  |;;|  \_c_/
          |____o|##|o____|
           \ ___|~~|___ /
            '>--------<'
            {==_==_==_=}
            {= -=_=-_==}
            {=_=-}{=-=_}
            {=_==}{-=_=}
            }~~~~""~~~~{
       jgs  }____::____{
           /`    ||    `\ 
           |     ||     |
           |     ||     |
           |     ||     |
           '-----''-----'""",
      minSize  = 10,    # min leaf size
      depthMin= 2,      # no pruning till this depth
      depthMax= 10,     # max tree depth
      wriggle = 0.2,    # min difference of 'better'
      prune   = True,   # pruning enabled?
      b4      = '|.. ', # indent string
      verbose = False,  # show trace info?
      hedges  = 0.38,   # strict=0.38,relax=0.17)
      seed    = 1
  ).update(**also)
"""

And a global to hold the top-level tree of the defaults.

"""
The=defaults()


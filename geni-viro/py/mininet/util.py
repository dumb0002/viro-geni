import re

def vid2hex(vid, length=0):
  """ Convertes an integer vid to a hex string """
  vid = hex(vid)[2:]
  if length > len(vid):
    vid = '0' * (length - len(vid)) + vid
  return vid

def vid2dpid(vid, dpidLen):
  """ Converts an integer vid to a switch data path id """
  dpid = vid2hex(vid, length=dpidLen)
  return dpid

def itersplit(s, sep=None):
  """ Splits s on sep returning an iterator """
  exp = re.compile(r'\s+' if sep is None else re.escape(sep))
  pos = 0
  while True:
    m = exp.search(s, pos)
    if not m:
      if pos < len(s) or sep is not None:
          yield s[pos:]
      break
    if pos < m.start() or sep is not None:
      yield s[pos:m.start()]
    pos = m.end()

def itertokens(fname, sep=" ", func=None):
  """ Creates an iterator over "fname" lines with splitting each line on "sep", and 
  then applies "func" to each element """
  with open(fname, 'r') as fin:
    for line in fin:
      if line.startswith('#'):
        continue
      
      l = line.strip()
      if l == "":
        continue
      
      if func:
        l = map(func, itersplit(l, sep))
      else:
        l = l.split(sep)
        
      yield l
      

class Struct:
  """ A C like structure """
  def __init__(self, **entries):
    self.__dict__.update(entries)
      

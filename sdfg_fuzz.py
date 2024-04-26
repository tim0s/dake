import os
import re
import dace
import random
import argparse

class RandomSDFGGen:

  def __init__(self, outfile="last_sdfg.py"):
    self.sdfg = None
    self.node2name = {}
    self.outfile = outfile

    # clear outfile
    if os.path.exists(self.outfile):
      os.remove(self.outfile)

  def add_command(self, cmd):
    """Log a call to the SDFG API (or other interaction with DaCe) to the defined output file."""
    with open(self.outfile, "a") as f:
      print(cmd, file=f)

  def add_named_obj(self, obj, name):
    """Establish mapping between obj and name so that we can find the object by its name and vice versa"""
    if obj in self.node2name.keys():
      raise ValueError("Tried adding an object which already exists!")
    if name in self.node2name.values():
      raise ValueError("Tried adding a name which already exists!")
    self.node2name[obj] = name

  def get_obj_name(self, obj):
    """Retrieve the name of an object which was added previously by add_named_obj"""
    if obj not in self.node2name.keys():
      raise ValueError("Lookup for object which has not been added!")
    return self.node2name[obj]

  def get_random_data(self, state):
    data = state.sdfg.arrays
    key, val = random.choice(list(data.items()))
    return key

  def choose_src_elem(self, state):
    nodes = list(state.all_nodes_recursive())
    return nodes[random.randrange(0, len(nodes))][0]

  def choose_src_conn(self, node):
    conns = list(node.out_connectors)
    if len(conns) == 0:
      return None
    return conns[random.randrange(0, len(conns))]

  def choose_dst_elem(self, state):
    nodes = list(state.all_nodes_recursive())
    return nodes[random.randrange(0, len(nodes))][0]

  def choose_dst_conn(self, node):
    conns = list(node.in_connectors)
    if len(conns) == 0:
      return None
    return conns[random.randrange(0, len(conns))]

  def print_as_py(self, obj): 
    # hack because None should be None but connector names should be strings in quotes
    if obj is None:
      return None
    else:
      return f"\"{str(obj)}\""

  def generate_random_element(self, state, idx):
    elem_types = ['raccess', 'waccess', 'mentry', 'mexit', 'tasklet']
    elem_type = elem_types[random.randrange(0,len(elem_types))]
    r = None
    if elem_type == 'raccess':      
      src = self.get_random_data(state)      
      self.add_command(f"read_{idx} = state.add_read(\"{src}\")")
      read = state.add_read(src)      
      self.add_named_obj(read, f"read_{idx}")      
    if elem_type == 'waccess':      
      dst = self.get_random_data(state)
      self.add_command(f"write_{idx} = state.add_write(\"{dst}\")")   
      write = state.add_write(dst)      
      self.add_named_obj(write, f"write_{idx}")      
    if elem_type == "mentry":      
      self.add_command(f"mentry_{idx}, mexit_{idx} = state.add_map(\"map_{idx}\", dict(i=\"0:9\"))")      
      mentry, mexit = state.add_map("map_"+str(idx), dict(i="0:9"))      
      self.add_named_obj(mentry, f"mentry_{idx}")      
      self.add_named_obj(mexit, f"mexit_{idx}")   
      self.add_command(f"mentry_{idx}.add_in_connector(\"IN_0\")")      
      mentry.add_in_connector("IN_0")      
      self.add_command(f"mentry_{idx}.add_out_connector(\"OUT_0\")")      
      mentry.add_out_connector("OUT_0")      
      self.add_command(f"mexit_{idx}.add_in_connector(\"IN_0\")")     
      mexit.add_in_connector("IN_0")      
      self.add_command(f"mexit_{idx}.add_out_connector(\"OUT_0\")")      
      mexit.add_out_connector("OUT_0")
    if elem_type == "tasklet":      
      self.add_command(f"tasklet_{idx} = state.add_tasklet(\"task_{idx}\", {'in0', 'in1'}, {'out0', 'out1'}, \"out0 = in0 + in1; out1 = in0 - in1;\")")    
      tlet = state.add_tasklet("task_"+str(idx), {'in0', 'in1'}, {'out0', 'out1'}, "out0 = in0 + in1; out1 = in0 - in1;")       
      self.add_named_obj(tlet, f"tasklet_{idx}")     
  

  def generate_sdfg(self, name="foo"):
    # create sdfg
    self.add_command(f"sdfg = dace.SDFG(\"{name}\")")
    self.sdfg = dace.SDFG(name)
    self.add_named_obj(self.sdfg, name)

    # create state
    self.add_command(f"state = sdfg.add_state()")
    s = self.sdfg.add_state()
    self.add_named_obj(s, "state")

    # add some random data containers
    for idx in range(1, 3):
      self.add_command(f"sdfg.add_array(\"data_{idx}\", shape=(10, ), dtype=dace.float32)")
      self.sdfg.add_array("data_"+str(idx), shape=(10, ), dtype=dace.float32)

    # add some random elems
    for idx in range(1, 10):
      e = self.generate_random_element(s, idx)

    # add some random memlet paths
    for i in range(1, 30):
      elem_src = self.choose_src_elem(s)
      elem_dst = self.choose_dst_elem(s)
      conn_src = self.choose_src_conn(elem_src)
      conn_dst = self.choose_dst_conn(elem_dst)
      name_state = self.get_obj_name(s)
      name_src = self.get_obj_name(elem_src)
      name_dst = self.get_obj_name(elem_dst)
      name_src_conn = self.print_as_py(conn_src)
      name_dst_conn = self.print_as_py(conn_dst)
      self.add_command(f"{name_state}.add_edge({name_src}, {name_src_conn}, {name_dst}, {name_dst_conn}, dace.Memlet(data=\"bla\", subset='0:9'))")
      s.add_edge(elem_src, conn_src, elem_dst, conn_dst, dace.Memlet(data="bla", subset='0:9'))

    return self.sdfg



if __name__ == "__main__":

  parser = argparse.ArgumentParser(
    prog='sdfg_fuzz.py',
    description='Generate random SDFGs until we found one that generates an unxepected exception.',
    epilog='Written by Timo Schneider <timos@inf.ethz.ch>, 2024')
  parser.add_argument('-n', '--numruns', default=1000, help="Number of random SDFGs to generate.")
  parser.add_argument('-f', '--reprofile', default='repro.py', help="Filename of the last generated SDFG.")
  parser.add_argument('-v', '--validate', action='store_true', help="If this option is given, attempt to validate each SDFG.")
  parser.add_argument('-c', '--compile', action='store_true', help="If this option is given, attempt to compile each SDFG.")
  parser.add_argument('-s', '--simplify', action='store_true', help="If this option is given, attempt to simplify each SDFG.")
  parser.add_argument('-e', '--skip-exception', action='append', help="A regex pattern to match exceptions against, matching exceptions are ignored, can be given multiple times.")
  args = vars(parser.parse_args())


  for i in range(1, args['numruns']):
    sdfggen = RandomSDFGGen(args['reprofile'])
    try:
      sdfg = sdfggen.generate_sdfg()
      if args['validate']:
        sdfggen.add_command("sdfg.validate()")
        sdfg.validate()
      if args['compile']:
        sdfg.compile()
      if args['simplify']:
        sdfg.simplify()
    except Exception as e:
      ignore = False
      # if e matches any of the patterns indicated by the user, go on, otherwise grok
      for pattern in args['skip_exception']:
        p = re.compile(pattern)
        if p.match(str(e)):
          print(f"Exception matched pattern \"{pattern}\", ignoring.")
          ignore = True
      if ignore == False:
        raise e
        break
   





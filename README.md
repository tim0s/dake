Primitive SDFG Fuzzer
=====================

Generate random SDFGs using the "raw" DaCe SDFG API. Attempt to validate, compile and simplify them.
See where things break.

Usage:

```
python3 ./sdfg_fuzz.py --help
usage: sdfg_fuzz.py [-h] [-n NUMRUNS] [-f REPROFILE] [-v] [-c] [-s] [-e SKIP_EXCEPTION]

Generate random SDFGs until we found one that generates an unxepected exception.

options:
  -h, --help            show this help message and exit
  -n NUMRUNS, --numruns NUMRUNS
                        Number of random SDFGs to generate.
  -f REPROFILE, --reprofile REPROFILE
                        Filename of the last generated SDFG.
  -v, --validate        If this option is given, attempt to validate each SDFG.
  -c, --compile         If this option is given, attempt to compile each SDFG.
  -s, --simplify        If this option is given, attempt to simplify each SDFG.
  -e SKIP_EXCEPTION, --skip-exception SKIP_EXCEPTION
                        A regex pattern to match exceptions against, matching exceptions are ignored, can be given multiple times.

Written by Timo Schneider <timos@inf.ethz.ch>, 2024
```

To simply generate SDFGs and do noting with them (this would discover bugs in the generation API itself, i.e., https://github.com/spcl/dace/issues/1558 was found this way)
```
python3 ./sdfg_fuzz.py
```
With the current DaCe master this finds no bugs when running a few seconds. Good. We can also try to validate the generated SDFGs:
```
python3 ./sdfg_fuzz.py --validate
Traceback (most recent call last):
  File "/home/timos/Work/DaKe/./sdfg_fuzz.py", line 222, in <module>
    raise e
  File "/home/timos/Work/DaKe/./sdfg_fuzz.py", line 209, in <module>
    sdfg.validate()
  ...
  File "/home/timos/Work/dace/dace/sdfg/validation.py", line 344, in validate_state
    scope = state.scope_dict()
            ^^^^^^^^^^^^^^^^^^
  File "/home/timos/Work/dace/dace/sdfg/state.py", line 577, in scope_dict
    raise ValueError('Found cycles in state %s: %s' % (self.label, cycles))
ValueError: Found cycles in state state: [[MapExit (map_2[i=0:9])], [MapEntry (map_8[i=0:9])], [Tasklet (task_9)], [MapEntry (map_8[i=0:9]), MapExit
...
```
which will fail almost immediately since we generate a lot of SDFGs which are malformed (we TRY to generate random ones to discover bugs). We can tell the fuzzer to ignore this kind of error
using the exclude pattern (a regex which must match the beginning of the exception converted to a Python string):
```
python3 ./sdfg_fuzz.py --validate -e "Found cycles in state"
```
This will likely trigger another exception about cycles (one could argue that there should be only one, but hey, if that are the bugs you are worried about maybe try different code).
Let's exclude that as well. You can add as many exclude patterns as you want.
```
python3 ./sdfg_fuzz.py --validate -e "Found cycles" -e "State should be acyclic"
Traceback (most recent call last):
  File "/home/timos/Work/DaKe/./sdfg_fuzz.py", line 209, in <module>
    sdfg.validate()
  File "/home/timos/Work/dace/dace/sdfg/sdfg.py", line 2350, in validate
    validate_sdfg(self, references, **context)
 ...
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/timos/Work/dace/dace/sdfg/graph.py", line 654, in out_edges
    return list(self._nodes[node][1].values())
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
RecursionError: maximum recursion depth exceeded while calling a Python object
```
This looks interesting, I would argue that this is a bug [https://github.com/spcl/dace/issues/1562], this error does not tell me if the SDFG is ill-formed or not.

The fuzzer produces a ```repro.py``` output file which contains all the API calls which lead to the exception.
But this file is big, with the current default generation settings (which cannot even be changed yet) about 60 lines.
We can use the ```reducer.py``` tool which successifly tries to comment out lines of code to reduce the SLOC length.
```
python3 ./repro.py # make sure this actually reproduces the bug, i.e., add missing includes
python3 ./reducer.py --infile repro.py --outfile min_repro.py
current shortest example is 56 lines long
similarity was 10.881678138315309, threshold is set to 90  # by default reducer uses string similarity on stdout + stderr
similarity was 11.267605633802813, threshold is set to 90  # to judge if behaviour is equivalent --- this runs for about
...                                                        # a minute at the moment and should be made way smarter 
cat min_repro.py 
import dace
sdfg = dace.SDFG("foo")
state = sdfg.add_state()
mentry_2, mexit_2 = state.add_map("map_2", dict(i="0:9"))
mentry_4, mexit_4 = state.add_map("map_4", dict(i="0:9"))
tasklet_7 = state.add_tasklet("task_7", ('in0', 'in1'), ('out0', 'out1'), "out0 = in0 + in1; out1 = in0 - in1;")
tasklet_9 = state.add_tasklet("task_9", ('in0', 'in1'), ('out0', 'out1'), "out0 = in0 + in1; out1 = in0 - in1;")
state.add_edge(tasklet_7, "out0", mentry_2, "IN_0", dace.Memlet(data="bla", subset='0:9'))
state.add_edge(mentry_2, "OUT_0", tasklet_9, "in1", dace.Memlet(data="bla", subset='0:9'))
state.add_edge(tasklet_9, "out0", mentry_4, "IN_0", dace.Memlet(data="bla", subset='0:9'))
state.add_edge(mentry_4, "OUT_0", mentry_2, "IN_0", dace.Memlet(data="bla", subset='0:9'))
sdfg.validate()
```
If we also ignore this exception we don't find more bugs with our current completely dumb SDFG generation approach and have time to look at
the statistics generated by the fuzzer.
```
python3 ./sdfg_fuzz.py --validate -e "Found cycles" -e "State should be acyclic" -e "maximum recursion"
SDFGFuzz running since 12.46 seconds.
Planned to run 1000 iterations.
Sucessful runs:
  generate: 810
  validate: 0
  compile: 0 (compile disabled by command-line arg)
  simplify: 0 (simplify disabled by command-line arg)
Ignored exceptions:
  Found cycles: 722
  State should be acyclic: 38
  maximum recursion: 50
```
We can see that most of our discovered "problems" are cyclic SDFGs, so when I have time to code on this again I will add a feature to set the
probability of an edge being added which will lead to a cycle.

Some open questions I want to answer with this:
* How can we make DaCe more robust using tools like testing, fuzzing, verification?
* Can we build fuzzers for SDFGs or other IRs which give usable feedback on what was/wasn't tested?
* Can we drive fuzzing from semantics, i.e., especially test "underspecified" semenatics?

Semantics of DaCe in K
======================

Install the K-framework 
```
bash <(curl https://kframework.org/install)
kup install k
```

So far we have a rough syntax of a language to build an SDFG:
```
kompile --main-module SDFG grammar.k
kast example.sdfg
```

Next steps:
-----------

* Add missing parts of SDFG API? (Views, References, Memlet-subsets, tasklet code, WCR)
* Use the K grammar to generate inputs (why can K not do this out-of-the-box?)
* Use K rules to interpret sdfg files and turn them into a graph datastructure within a K environment
* Define semantics of SDFG graphs for the interpretation of SDFGs


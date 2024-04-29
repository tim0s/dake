module SDFG

    syntax SDFG ::= SDFG SdfgDef 
                  | SDFG SdfgUse 
                  | SdfgDef
                  | SdfgUse
    syntax SdfgDef ::= "SDFG" "(" Id ")"
    syntax SdfgRef ::= Id "."
    syntax SdfgUse ::= SdfgRef StateDef
                      | SdfgRef DataDef 
                      | SdfgRef InsterstateDef 
                      | SdfgRef SymbolDef
                      | SdfgRef StateUse
    syntax StateUse ::= StateRef DataDef
                       | StateRef MapDef
                       | StateRef ReadDef
                       | StateRef WriteDef
                       | StateRef MemletDef
                       | StateRef NodeUse
    syntax StateRef ::= Id "."
    syntax StateDef ::= "STATE" "(" Id ")"
    syntax DataDef ::= "DATA" "(" Id "," Shape "," Dtype ")"
    syntax InsterstateDef::= SdfgRef "INTERSTATE_EDGE" "(" Id "," Id "," Condition "," Assignments ")"
    syntax SymbolDef ::= SdfgRef "SYMBOL" "(" Id "," Dtype ")"
                        | SdfgRef "SYMBOL" "(" Id "," Dtype "," Value ")"
    syntax MapDef ::= "MAP" "(" Id "," "[" NamedRanges "]" ")"
    syntax ReadDef ::= "READ" "(" Id "," Id ")"
    syntax WriteDef ::= "WRITE" "(" Id "," Id ")"
    syntax TaskletDef ::= "TASKLET" "(" Id "," Code ")"
    syntax NodeRef ::= StateRef "." "NODE" "(" Id ")"
    syntax MemletDef ::= "MEMLET" "(" Id "," Id ")" //what about subset, other_subset?
    syntax NodeUse ::= NodeRef InconnDef
                     | NodeRef OutconnDef
    syntax InconnDef ::= "IN_CONNECTOR" "(" Id ")"
    syntax OutconnDef ::= "OUT_CONNECTOR" "(" Id ")"
    syntax Shape ::= "[" Pnats "]"
    syntax Assignments ::= Assignment
                         | Assignment ";" Assignments
    syntax Assignment ::= Id "=" Value
    syntax NamedRanges ::= NamedRange "," NamedRanges
                         | NamedRange
    syntax NamedRange ::= Id "=" Nat ":" Nat ":" Nat
                        | Id "=" Nat ":" Nat 
    syntax Dtype ::= r"[u]?int(8|16|32|64)" [token]
                   | r"float(32|64)"        [token]
    syntax Condition ::= Id | "True" | "False" | "(" Condition ")" | "(" Condition "&" Condition ")" 
    syntax Nat ::= "-" Pnat
                 | Pnat
    syntax Pnat ::= r"[1-9][0-9]*" [token]
                  | "0" [token]
    syntax Pnats ::= Pnats "," Pnat
                   | Pnat
    syntax Value ::= Nat
                   | Float
    syntax Float ::= r"0|[1-9][0-9]*.?[0-9]*" [token]
    syntax Id ::= r"[a-zA-Z]+[a-zA-Z0-9_]*"   [token]
    syntax Code ::= "code" //define small imperative language without loops or functions

endmodule
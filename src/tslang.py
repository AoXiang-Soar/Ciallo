#import tree_sitter_c as tsc
#import tree_sitter_cpp as tscpp
import tree_sitter_java as tsj
#import tree_sitter_python as tspy
from tree_sitter import Language

#PYTHON = Language(tspy.language())
JAVA = Language(tsj.language())
#C = Language(tsc.language())
#CPP = Language(tscpp.language())
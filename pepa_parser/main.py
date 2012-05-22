from pyparsing import Word, alphas, ParseException, Literal \
, Combine, Optional, nums, Or, Forward, ZeroOrMore, OneOrMore, StringEnd, alphanums, alphas, ZeroOrMore, restOfLine
import math

class Node():
    left, right, data = None, None, 0

    def __init__(self,data):
        self.right = None
        self.left = None
        self.data = data

class PTree():
    nodes = []
    root = Node("MODEL")
    last_node = None
    
    def __init__(self):
        self.nodes.append(self.root)

    def add_node(self,node):
        self.last_node = node 
        self.nodes.append(node)

class Model():
    processes = []
    PTree = PTree()
    costam = ""

model = Model()

logging = False

def createActivity(tokens):
    print("ACT",tokens[0])
    model.costam += " ACT "

def createConstant(tokens):
    print("RMDEF",tokens[0])
    model.costam += " = "+tokens[0]

def createPrefix(tokens):
    print("PREFIX",tokens[3])
    model.costam += " DOT "+tokens[3]

def createChoice(tokens):
    print("CHOICE", tokens)
    model.costam += " + "+tokens[1]

def log(string, msg="",prepend="log"):
    if logging:  print(prepend,msg,string)

def error(string):
    print("ERROR: ", string)

varStack = {}

def assignVar(toks):
    log(toks, "VAR")
    varStack[toks[0]] = toks[2]

def checkVar(toks):
    try:
        if toks[0] not in ("infty", "T", "tau"):
            varStack[toks[0]]
    except:
        error(toks[0]+" Rate not defined")
        exit()

## Tokens
point = Literal('.')
prefix_op = Literal('.')
choice_op = Literal('+')
parallel = Literal("||")
ident = Word(alphas, alphanums+'_')
lpar = Literal('(').suppress()
rpar = Literal(')').suppress()
define = Literal('=')
semicol = Literal(';').suppress()
col = Literal(',').suppress()
number = Word(nums)
integer = number
floatnumber = Combine( integer + Optional( point + Optional(number)))
passiverate = Word('infty') | Word('T')
internalrate = Word('tau')
peparate = (floatnumber | internalrate | passiverate | ident).setParseAction(checkVar)
peparate_indef = floatnumber | internalrate | passiverate 
sync = Word('<').suppress() + ident + ZeroOrMore(col + ident) + Word('>').suppress()
coop_op = parallel | sync

## RATES Definitions
ratedef = (ident + define + peparate_indef).setParseAction(assignVar) + semicol

## PEPA Grammar 
expression = Forward()
activity = (ident + col + peparate).setParseAction(createActivity)
process = lpar + activity + rpar | ident | lpar + expression + rpar
prefix = (process + ZeroOrMore(prefix_op + process)).setParseAction(createPrefix)
choice = (prefix + ZeroOrMore(choice_op + prefix)).setParseAction(createChoice)
expression << choice + ZeroOrMore(coop_op + choice)
rmdef = (ident + define + expression + semicol).setParseAction(createConstant)

expr = Forward()
atom_proc = lpar + expr + rpar | ident
expr << atom_proc + ZeroOrMore(coop_op + atom_proc)
system_eq =  expr 

pepa = ZeroOrMore(ratedef) + ZeroOrMore(rmdef) + system_eq

pepacomment = '//' + restOfLine
pepa.ignore(pepacomment)

if __name__=="__main__":
    with open("simple.pepa","r") as f: 
         try:
             tokens = pepa.parseString(f.read())
             print(tokens)
             print(model.costam)
         except ParseException as e:
            error(e)

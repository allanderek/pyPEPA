#/usr/bin/env python
import logging
import sys
from parsing.pepa_treewalker import PEPATreeWalker
from parsing.comp_state_space_graph import ComponentSSGraph
from pylab import figure, axes,pie,title, show
from parsing.parser import PEPAParser

class ComponentStateVisitor():

    def __init__(self, graph):
        self.graph = graph
        self.visited = []
        self.dot = ""

    def generate_ss(self, node, comp):
        self.visited = []
        return self._visit_for_ss(node,comp)

    def _visit_for_ss(self, node, comp):
        self.visited.append(node)
        comp.ss[node] = self.graph.ss[node]
        transitions = self.graph.ss[node].transitions
        for tran in transitions:
            if tran.action in self.graph.shared_actions:
                comp.shared.append( (tran.action, tran.rate) )
            comp.activities.append( (tran.action, tran.rate) )
            if tran.to not in self.visited:
                self._visit_for_ss(tran.to, comp)
        return comp


    def get_dot(self, node):
        with open("dots/"+node + ".dot", "w") as f:
            self.dot = "digraph " + node + "{\n"
            self._visit_dot(node)
            self.dot += "}\n"
            f.write(self.dot)
        return self.dot

    def _visit_dot(self, node):
        self.visited.append(node)
        transitions = self.graph.ss[node].transitions
        for tran in transitions:
            if tran.action in self.graph.shared_actions:
                self.dot += "\"" + node + "\" -> \"" + tran.to + "\"" + \
                " [label=\"(" + tran.action + "," + tran.rate + ")\" \
                fontsize=10, fontcolor=red]\n"
            else:
                self.dot += "\"" + node + "\" -> \"" + tran.to + "\"" + " [label=\"(" + tran.action + "," + tran.rate + ")\" fontsize=10]\n"
            if tran.to not in self.visited:
                self._visit_dot(tran.to)

class PEPAModel():
    """
        Representation of a final PEPA model, everything needed to derive CTMC
        - state spaces of components that are present in a system equation
        - rate definitions
        - system equation
    """
    def __init__(self, modelfile):
        """ Create PEPA model instance and fill the fields

        Keyword arguments:
        modelfile --- path to the model file
        """
        self.processes = {}
        self.systemeq = None
        self.rate_definitions = {}
        self.components = {}
        # from BU alg, get rid of it
        self.tw = None
        self.log = logging.getLogger(__name__)
        self.ss = None
        self._parse_read_model(modelfile)
        self._prepare_trees()
        self._prepare_systemeq()
        self._system_eq_BU()


    def _system_eq_BU(self):
        """ Derives global state space """
        self.ss.comp_ss = self.tw.graph.ss
        (res,actset) = self.ss.derive()
        from solvers.ctmc import ctmc, create_matrix, vector_mult
        steady = (ctmc(create_matrix(res)))
        print(steady)
        print("Statespace has " + str(len(steady)) + " states")
        print("Throughoutput")
        figure(1, figsize=(6,6))
        labels = []
        x = []
        for action in actset.keys():
            acts = actset[action]
            vect = [0] * len(steady)
            for aaa in acts:
                #0 is state, 1 is rate
                vect[aaa[0]-1] = aaa[1]
            labels.append(action + "\n" +  str( vector_mult(steady, vect)))
            x.append(vector_mult(steady, vect))
            print(action + "\t" +  str ( vector_mult(steady, vect)) )
        pie(x, labels=labels)
        title("Throughoutput")
        #show()


    def _generate_components(self):
        """
        Generates state space graphs for every component
        in the model into components dict
        """
        visitor = ComponentStateVisitor(self.tw.graph)
        for comp in set(self.ss.components):
            self.components[comp.data] = ComponentSSGraph(comp.data)
            self.components[comp.data] = visitor.generate_ss(comp.data, self.components[comp.data])

    def _prepare_systemeq(self):
        """
        Returns StateSpace object
        """
        self.log.debug("Preparing systemeq")
        self.ss = self.tw.derive_systemeq(self.systemeq)

    def _parse_read_model(self, modelfile):
        """ Reads model file and parses it.
        """
        with open(modelfile, "r") as f:
            modelfile = f.read()
        try:
            parser = PEPAParser(False)
            (self.processes, self.rate_definitions, self.systemeq) = parser.parse(modelfile)
            self.tw = PEPATreeWalker(self.rate_definitions)
        except Exception as e:
            self.log.debug(e)
            print("Parsing error : " + str(e) )
            sys.exit(1)

    def _prepare_trees(self):
        """ Here ss graphs of every process is derived from AST trees
        """
        for node in self.processes.values():
            self.tw.derive_processes_ss(node, self.rate_definitions)

    def generate_dots(self):
        """ Generates dot files to browse with e.g. xdot """
        self._generate_components()
        visitor = ComponentStateVisitor(self.tw.graph)
        for comp in set(self.ss.components):
            visitor.get_dot(comp.data)



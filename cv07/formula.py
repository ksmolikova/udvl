import cnf

class Formula(object):
    def __init__(self, subs = []):
        self.m_subf = subs
    def subf(self):
        return self.m_subf
    def eval(self, i):
        return False
    def toString(self):
        return "INVALID"
    def toCnf(self):
        """ Vrati reprezentaciu formuly v CNF tvare. """
        return cnf.Cnf()

class Variable(Formula):
    def __init__(self, name):
        Formula.__init__(self)
        self.name = name
    def eval(self, i):
        return i[self.name]
    def toString(self):
        return self.name
    def toCnf(self):
        """ Vrati reprezentaciu formuly v CNF tvare. """
        return cnf.Cnf([cnf.CnfClause([cnf.CnfLit(self.name)])])

class Negation(Formula):
    def __init__(self, orig):
        Formula.__init__(self, [orig])
    def originalFormula(self):
        return self.subf()[0]
    def eval(self, i):
        return not self.originalFormula().eval(i)
    def toString(self):
        return "-%s" % (self.originalFormula().toString())

    def doProduct(self, clauses, level):
        if level < len(clauses):
            for lit in clauses[level]:
                self.currentLiterals.append(-lit) #pridame negovany literal
                self.doProduct(clauses, level+1)
                self.currentLiterals.pop()
        else:
            self.resCnf.append(cnf.CnfClause(self.currentLiterals))

    def toCnf(self):
        origcnf=self.originalFormula().toCnf()
        self.resCnf=cnf.Cnf()
        self.currentLiterals= []
        self.doProduct(origcnf, 0)
        return self.resCnf
    
class Disjunction(Formula):
    def __init__(self, subs):
        Formula.__init__(self, subs)
    def eval(self, i):
        for f in self.subf():
            if f.eval(i):
                return True
        return False
    def toString(self):
        return '(' + '|'.join([f.toString() for f in self.subf()]) + ')'

    def doProduct(self, cnfs, level):
        if level < len(cnfs):
            for clause in cnfs[level]:
                # pridame do currentClause literaly z cnfs[level]
                self.currentClause.extend(clause)
                self.doProduct(cnfs, level+1)
                for i in range(len(clause)):
                    self.currentClause.pop()
        else:
            self.resCnf.append(cnf.CnfClause(self.currentClause))

    def toCnf(self):
        origCnfs = []
        for sf in self.subf():
            origCnfs.append(sf.toCnf())
        self.resCnf = cnf.Cnf()
        self.currentClause=[]
        self.doProduct(origCnfs, 0)
        return self.resCnf
    
class Conjunction(Formula):
    def __init__(self, subs):
        Formula.__init__(self, subs)
    def eval(self, i):
        for f in self.subf():
            if not f.eval(i):
                return False
        return True
    def toString(self):
        return '(' + '&'.join([f.toString() for f in self.subf()]) + ')'

    def toCnf(self):
        """ Vrati reprezentaciu formuly v CNF tvare. """
        c=cnf.Cnf()
        for sub in self.subf():
            c.extend(sub.toCnf())
        return c

class Binary(Formula):
    def __init__(self, left, right, conj):
        Formula.__init__(self, [left, right])
        self.conj = conj
    def left(self):
        return self.subf()[0]
    def right(self):
        return self.subf()[1]
    def toString(self):
        return '(%s%s%s)' % (self.left().toString(), self.conj, self.right().toString())

class Implication(Binary):
    def __init__(self, left, right):
        Binary.__init__(self, left, right, '=>')
    def eval(self, i):
        return (not self.left().eval(i)) or self.right().eval(i)
    def toCnf(self):
        return Disjunction([Negation(self.left()), self.right()]).toCnf()

class Equivalence(Binary):
    def __init__(self, left, right):
        Binary.__init__(self, left, right, '<=>')
    def eval(self, i):
        return self.left().eval(i) == self.right().eval(i)
    def toCnf(self):
        return Conjunction([Implication(self.left(), self.right()), Implication(self.right(), self.left()) ]).toCnf()
# vim: set sw=4 ts=4 sts=4 et :

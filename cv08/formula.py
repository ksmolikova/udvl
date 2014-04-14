import tableau

class Formula(object):
    def __init__(self, subs = []):
        self.m_subf = subs
    def subf(self):
        return self.m_subf
    def eval(self, i):
        return False
    def toString(self):
        return "INVALID"

    def signedSubf(self, sign):
        """ Vrati oznacene podformuly tejto formuly, ak by tato formula bola oznacena ako sign.

        Ak by tato formula bola implikacia a sign by bolo True, tak by podla tabloveho
        pravidla pre 'T A->B'  vratila zoznam [ (False, self.left()),  (True, self.right()) ].

        Ak by tato formula bola implikacia a sign by bolo False, tak by podla tabloveho
        pravidla pre 'F A->B'  vratila zoznam [ (True, self.left()),  (False, self.right()) ].

        Negacia je vzdy formula typu ALPHA s jednou podformulou.
        Premenna je formula typu ALPHA so ziadnou podformulou.

        Pozor: konjunkcia a disjunkcia mozu mat viac ako dve podformuly!
        """
        return []

    def getType(self, sign):
        """ Vrati typ formuly (tableau.ALPHA alebo tableau.BETA), ak by tato formula bola oznacena ako sign.

        Ak by tato formula bola implikacia a sign by bolo True, tak by vratila
        tableau.BETA, pretoze tablove pravidlo pre 'T A->B' je typu beta.

        Ak by tato formula bola implikacia a sign by bolo False, tak by vratila
        tableau.ALPHA, pretoze tablove pravidlo pre 'F A->B' je typu alfa.

        Negacia je vzdy formula typu ALPHA s jednou podformulou.
        Premenna je formula typu ALPHA so ziadnou podformulou.
        """
        return None

class Variable(Formula):
    def __init__(self, name):
        Formula.__init__(self)
        self.name = name
    def eval(self, i):
        return i[self.name]
    def toString(self):
        return self.name
    def getType(self,sign):
        return tableau.ALPHA

class Negation(Formula):
    def __init__(self, orig):
        Formula.__init__(self, [orig])
    def originalFormula(self):
        return self.subf()[0]
    def eval(self, i):
        return not self.originalFormula().eval(i)
    def toString(self):
        return "-%s" % (self.originalFormula().toString())
    def getType(self,sign):
        return tableau.ALPHA
    def signedSubf(self,sign):
        return [(not sign, self.originalFormula())]

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
    def getType(self,sign):
        if sign:
            return tableau.BETA
        else:
            return tableau.ALPHA
        
    def signedSubf(self, sign):
        return [(sign, f) for f in self.subf()]
    

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
    
    def getType(self,sign):
        if sign:
            return tableau.ALPHA
        else:
            return tableau.BETA
        
    def signedSubf(self, sign):
        return [(sign, f) for f in self.subf()]

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
    def getType(self,sign):
        if sign:
            return tableau.BETA
        else:
            return tableau.ALPHA
        
    def signedSubf(self, sign):
        return [(not sign, self.left()),(sign, self.right())]

class Equivalence(Binary):
    def __init__(self, left, right):
        Binary.__init__(self, left, right, '<=>')
    def eval(self, i):
        return self.left().eval(i) == self.right().eval(i)
    def getType(self,sign):
        if sign:
            return tableau.ALPHA
        else:
            return tableau.BETA
        
    def signedSubf(self, sign):
        return [(sign, Implication(self.left(),self.right())),(sign, Implication(self.right(),self.left()))]

# vim: set sw=4 ts=8 sts=4 et :

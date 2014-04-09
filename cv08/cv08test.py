#!/bin/env python3

import traceback
import time
import itertools

"""
    Testovaci program pre TableauBuilder
"""


""" Nastavte na True ak chcete aby testy zastali na prvej chybe. """
stopOnError = False

from builder import TableauBuilder
from tableau import Node, signedFormToString, ALPHA, BETA
from formula import Formula, Variable, Negation, Conjunction, Disjunction, Implication, Equivalence

def printException():
    print('ERROR: Exception raised in toCnf:\n%s\n%s\n%s' % (
        '-'*20,
        traceback.format_exc(),
        '-'*20)
    )

def now():
    try:
       return time.perf_counter() # >=3.3
    except AttributeError:
       return time.time() # this is not monotonic!

class FailedTestException(BaseException):
    pass

class BadTableauException(BaseException):
    pass

class Tester(object):
    def __init__(self):
        self.tested = 0
        self.passed = 0
        self.case = 0
        self.closed = 0
        self.size = 0
        self.time = 0

    def compare(self, result, expected, msg):
        self.tested += 1
        if result == expected:
            self.passed += 1
            return True
        else:
            print("Failed: %s:" %  msg)
            print("    got %s  expected %s" % (repr(result), repr(expected)))
            print("")
            return False

    def status(self):
        print("TESTED %d" % (self.tested,))
        print("PASSED %d" % (self.passed,))
        print("SUM(closed) %d" % (self.closed,))
        print("SUM(time) %f" % (self.time,))
        print("SUM(size) %d" % (self.size,))
        if self.tested == self.passed:
            print("OK")
        else:
            print("ERROR")
    
    def closedToString(self, closed):
        return "CLOSED" if closed else "OPEN"
    
    def typeToString(self, fType):
        if fType == ALPHA:
            return "ALPHA"
        if fType == BETA:
            return "BETA"
        return str(fType)
    
    def testSignedForm(self, f, expTypeT, expSfsT):
        self.case += 1
        self.tested += 1
        print("CASE %d: %s" % (self.case, f.toString()))
        sfsT = frozenset()
        sfsF = frozenset()
        try:
            start = now()
            typeT = f.getType(True)
            typeF = f.getType(False)
            sfsT = frozenset([signedFormToString(sf) for sf in f.signedSubf(True)])
            sfsF = frozenset([signedFormToString(sf) for sf in f.signedSubf(False)])
            duration = now() - start
        except KeyboardInterrupt:
            raise KeyboardInterrupt()
        except:
            printException()
            if stopOnError:
                raise FailedTestException()
            return
        
        expSfsF = frozenset([ signedFormToString((f, not s))
                              for f, s in expSfsT ])
        expSfsT = frozenset([ signedFormToString(sf) for sf in expSfsT ])
        sameT = expSfsT == sfsT
        sameF = expSfsF == sfsF
        okTypeT = len(expSfsT) <= 1 or expTypeT == typeT
        okTypeF = len(expSfsF) <= 1 or (ALPHA if expTypeT == BETA else BETA) == typeF

        self.time += duration

        if sameT and sameF and okTypeT and okTypeF:
            self.passed += 1
            print('PASSED:  time: %12.9f' % (duration,))
        else:
            print('FAILED:')
            fstrT = signedFormToString((f,True))
            fstrF = signedFormToString((f,False))
            if not okTypeT:
                print( 'Unexpected type of %s: %s\n' %
                        (fstrT, self.typeToString(typeT)) )
            if not okTypeF:
                print( 'Unexpected type of %s: %s\n' %
                        (fstrF, self.typeToString(typeF)) )
            if not sameT:
                print( 'Unexpected subformulas of %s:\n%s\n' %
                        (fstrT, '\n'.join(sfsT)) )
            if not sameF:
                print( 'Unexpected subformulas of %s:\n%s\n' %
                        (fstrF, '\n'.join(sfsF)) )
            if stopOnError:
                raise FailedTestException()
        print('')
        
    def testTableauStructure(self, node, ancestors, strSfs):
        strSf = signedFormToString((node.formula, node.sign))
        if node.source == None:
            if strSf not in strSfs:
                raise BadTableauException(
                    'Node (%d) has no source node and its formula not initial.' %
                    (node.number,)
                    )
        elif node.source not in ancestors:
            raise BadTableauException(
                'Node (%d) has source (%d) which is not one of its ancestors.' %
                (node.number, node.source.number,)
                )
        else:
            src = node.source
            parent = ancestors[-1]
            strSourceSubfs = [
                signedFormToString(sf)
                for sf in src.formula.signedSubf(src.sign)
                ]
            if strSf not in strSourceSubfs:
                raise BadTableauException(
                    'Node (%d) does not contain a subformula of (%d).' %
                    ( node.number, src.number )
                    )
            if (src.formula.getType(src.sign) == ALPHA and
                len(parent.children) != 1):
                raise BadTableauException(
                    'Node (%d) is a result of ALPHA rule for (%d) -- must have no siblings.' %
                    ( node.number, src.number )
                    )
            if True or (src.formula.getType(src.sign) == BETA and
                len(parent.children) != len(strSourceSubfs)):
                raise BadTableauException(
                    'Node (%d) should have %d siblings -- results of BETA rule for (%d).' %
                    ( node.number, len(strSourceSubfs)-1, src.number )
                    )
        ancestors.append(node)
        for child in node.children:
            self.testTableauStructure(child, ancestors, strSfs)
        ancestors.pop()

    def testTableau(self, expect_closed, sfs):
        self.case += 1
        self.tested += 1
        strSfs = [signedFormToString(sf) for sf in sfs ]
        print("CASE %d: %s" %
                (self.case,
                 '; '.join(strSfs)))
        tableau = Node(Variable(""), False)
        try:
            start = now()
            tableau = TableauBuilder().build(sfs)
            duration = now() - start
        except KeyboardInterrupt:
            raise KeyboardInterrupt()
        except:
            printException()
            if stopOnError:
                raise FailedTestException()
            return

        if not isinstance(tableau, Node):
            print('FAILED: not a tableau.Node: %s' % type(tableau))
            print()
            return

        closed = tableau.isClosed()
        badStructure = False
        try:
            self.testTableauStructure(tableau, [], strSfs)
        except BadTableauException as err:
            badStructure = str(err)
        except:
            printException()
            if stopOnError:
                raise FailedTestException()
            return

        size = tableau.numberOfNodes()

        self.time += duration
        self.size += size

        if closed:
            self.closed += 1

        if closed == expect_closed and not badStructure:
            self.passed += 1
            print('PASSED:  time: %12.9f   tableau size: %3d   %s' %
                    (duration, size, self.closedToString(closed)))
        else:
            print('FAILED: \n=====TABLEAU=====\n%s\n%s' %
                    (tableau.toString(), '='*13))
            if closed != expect_closed:
                print('Tableau is %s, but should be %s' %
                        (self.closedToString(closed), self.closedToString(expect_closed)))
            if badStructure:
                print(badStructure)
            if stopOnError:
                raise FailedTestException()
        print('')


t = Tester()

Not = Negation
Var = Variable
Impl = Implication

CLOSED = True
OPEN = False

def And(*args):
    if len(args)==1 and type(args[0]) is list:
        return Conjunction(args[0])
    return Conjunction(args)
def Or(*args):
    if len(args)==1 and type(args[0]) is list:
        return Disjunction(args[0])
    return Disjunction(args)

a = Var('a')
b = Var('b')
c = Var('c')
d = Var('d')


try:
    t.testSignedForm( a, None, [] )

    t.testSignedForm( Not(a), None, [ (a, False) ])

    t.testSignedForm( And([a, b]),
                      ALPHA,
                      [ (a, True), (b, True) ]
                    )
    
    t.testSignedForm( Or([a, b]),
                      BETA,
                      [ (a, True), (b, True) ]
                    )
    
    t.testSignedForm( And([a, b, c, d]),
                      ALPHA,
                      [ (a, True), (b, True), (c, True), (d, True) ]
                    )
    
    t.testSignedForm( Or([a, b, c, d]),
                      BETA,
                      [ (a, True), (b, True), (c, True), (d, True) ]
                    )
    
    t.testSignedForm( Or([a, Not(b), And(c, d) ]),
                      BETA,
                      [ (a, True), (Not(b), True), (And([c, d]), True) ]
                    )
    
    t.testSignedForm( Impl(a, b),
                      BETA,
                      [ (a, False), (b, True) ]
                    )
    
    t.testSignedForm( Equivalence(a, b),
                      ALPHA,
                      [ (Impl(a,b), True), (Impl(b,a), True) ]
                    )
    
    demorgan1 = Equivalence( Not( And([ a, b ]) ), Or([ Not(a), Not(b) ]) )
    t.testTableau(True, [ (demorgan1, False) ])
    
    demorgan2 = Equivalence( Not( Or([ a, b ]) ), And([ Not(a), Not(b) ]) )
    t.testTableau(True, [ (demorgan2, False) ])
    
    demorgan3 = Equivalence( Not( Or([ a, b, c ]) ),
                             And([ Not(a), Not(b), Not(c) ]) )
    t.testTableau(True, [ (demorgan3, False) ])
    
    contraposition = Equivalence( Impl(a, b), Impl( Not(b), Not(a) ) )
    t.testTableau(True, [ (contraposition, False) ])
    
    impl_impl_distrib = Impl( Impl(a, Impl(b, c)),
                              Impl( Impl(a, b), Impl(a, c) ) )
    t.testTableau(True, [ (impl_impl_distrib, False) ])
    
    impl_or = Equivalence( Impl(a, b), Or([ Not(a), b ]) )
    t.testTableau(True, [ (impl_or, False) ])
    
    impl_and = Equivalence( Impl(a, b), Not( And([ a, Not(b) ]) ) )
    t.testTableau(True, [ (impl_and, False) ])
    
    or_and_distrib = Equivalence( Or([ a, And([ b, c ]) ]),
                                  And([ Or([ a, b ]), Or([ a, c ]) ]) )
    t.testTableau(True, [ (or_and_distrib, False) ])
    
    bad_demorgan1 = Equivalence( Not( And([ a, b ]) ), Or([ a, b ]) )
    t.testTableau(False, [ (bad_demorgan1, False) ])
    
    bad_demorgan2 = Equivalence( Not( Or([ a, b ]) ), Or([ Not(a), Not(b) ]) )
    t.testTableau(False, [ (bad_demorgan2, False) ])
    
    bad_demorgan3 = Equivalence( Not( Or([ a, b, c ]) ),
                             And([ Not(a), b, Not(c) ]) )
    t.testTableau(False, [ (bad_demorgan3, False) ])
    
    bad_contraposition = Equivalence( Impl(a, b), Impl( b, a ) )
    t.testTableau(False, [ (bad_contraposition, False) ])
    
    bad_impl_impl_distrib = Impl( Impl(a, Impl(b, c)),
                              Impl( Impl(b, a), Impl(c, a) ) )
    t.testTableau(False, [ (bad_impl_impl_distrib, False) ])
    
    bad_impl_and = Equivalence( Impl(a, b), Not( And([ Not(a), b ]) ) )
    t.testTableau(False, [ (bad_impl_and, False) ])
    
    bad_or_and_distrib = Equivalence( Or([ a, And([ b, c ]) ]),
                                  Or([ And([ a, b ]), And([ a, c ]) ]) )
    t.testTableau(False, [ (bad_or_and_distrib, False) ])

    ax1 = Implication(Var('dazdnik'), Not(Var('prsi')))
    ax2 = Implication(
                    Var('mokraCesta'),
                    Or( [ Var('prsi'), Var('umyvacieAuto') ] ),
                )
    ax3 = Implication(Var('umyvacieAuto'), Not(Var('vikend')))
    cax1 = Conjunction([ ax1, ax2, ax3 ])
    conclusion = Implication(
                    And( [ Var('dazdnik'), Var('mokraCesta') ] ),
                    Not(Var('vikend')),
                )
    t.testTableau(True, [ (Conjunction([cax1, Not(conclusion)]), True) ])
    t.testTableau(True, [ (Implication(cax1, conclusion), False) ])
    t.testTableau(True, [ (cax1, True), (conclusion, False) ])
    t.testTableau(True, [ (ax1, True), (ax2, True), (ax3, True), (conclusion, False) ])
    t.testTableau(False, [ (cax1, True) ])
    t.testTableau(False, [ (conclusion, False) ])
    
    print("END")

except FailedTestException:
    print("Stopped on first failed test!")
finally:
    t.status()

# vim: set sw=4 ts=4 sts=4 et :

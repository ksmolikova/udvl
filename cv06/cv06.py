import os
import sys
sys.path[0:0] =[os.path.join(sys.path[0], '../examples/sat')]
import sat

P = 3 # pocet ludi
Agatha = 0
Butler = 1
Charles = 2

def killed(p1, p2):
    # p1 a p2 su vymenene
    # aby killed(X,Agatha) zodpovedalo 1, 2, 3
    return 0 * P * P + p2 * P + p1 + 1

def hates(p1, p2):
    return 1 * P * P + p1 * P + p2 + 1

def richer(p1, p2):
    return 2 * P * P + p1 * P + p2 + 1

def writeProblem(w):
    #niekto zabil agatu
    for x in range(P):
        w.writeLiteral(killed(x,Agatha))
    w.finishClause()
    #vrah nenavidi obete
    for x in range(P):
        for y in range(P):
            w.writeImpl(killed(x,y),hates(x,y))
    #vrah nie je bohatsi
    for x in range(P):
        for y in range(P):
            w.writeImpl(killed(x,y),-richer(x,y))
    #Z ľudí, ktorých Agáta nenávidí nie je taký, ktorého by Karol nenávidel. 
    for x in range(P):
        w.writeImpl(hates(Agatha,x),-hates(Charles,x))

    #Agáta nenávidí každého okrem komorníka. 
    for x in range(P):
        if x!=Butler:
            w.writeClause([hates(Agatha,x)])

    #Komorník nenávidí každého, kto nie je bohatší ako Agáta
    for x in range(P):
        w.writeImpl(-richer(x,Agatha),hates(Butler,x))
    
    #Komorník nenávidí každého, koho nenávidí Agáta
    for x in range(P):
        w.writeImpl(hates(Agatha,x),hates(Butler,x))

    #Niet toho, kto by nenávidel všetkých
    for x in range(P):
        for y in range(P):
            w.writeLiteral(-hates(x,y))
        w.finishClause()
        
    
    
            

w=sat.DimacsWriter("agatha-cnf.txt")
writeProblem(w)
s=sat.SatSolver()
satisfiable, solution=s.solve(w, "agatha-out.txt")

if not satisfiable:
    print("Teoria nekonzistentna")
    sys.exit(1)
    
w=sat.DimacsWriter("agatha-cnf-vrah.txt")
writeProblem(w)
vrah=Agatha
w.writeClause([-killed(vrah,Agatha)])

satisfiable, solution=s.solve(w, "agatha-vrah-out.txt")

if satisfiable:
    print("{} nie je vrahom, lebo {}".format(vrah,solution))
else:
    print("{} je vrahom".format(vrah))

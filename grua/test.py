
import shutil, os
from grua import *


global G

def run_tests():
    origVolPath = G.get('volumePath')
    G.set('volumePath', G.get('volumePath') + "_tests")

    shutil.rmtree(G.get('volumePath'), True)
    os.mkdir(G.get('volumePath'))



    shutil.rmtree(G.get('volumePath'), True)
    G.set('volumePath', origVolPath)



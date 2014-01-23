# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.
__author__="Sumner"
__version__="1.0"

class StackNode(object):
    def __init__(self,item,value):
        self._myitem = item
        self._myvalue = value
        self._nextNode = None

    def __str__(self):
        return str((self._myitem[0].id,self._myvalue))
    
    def setNext(self,nextNode):
        self._nextNode = nextNode

    def next(self):
        return self._nextNode

    def item(self):
        return self._myitem

    def value(self):
        return self._myvalue

class DataStructure(object):
    '''
    A simple stack which orders by racism severity
    '''
    def __init__(self,maxsize=-1):
        self._maxSize = maxsize
        self._topNode = None

    def hasNext(self):
        return self._topNode!=None

    def pop(self):
        top = self._topNode
        if self._topNode!=None:
            self._topNode = self._topNode.next()
        return top.item()

    def add(self,item,value):
        newNode = StackNode(item,value)
        if self._topNode==None:
            self._topNode = newNode
        elif value>self._topNode.value():
            newNode.setNext(self._topNode)
            self._topNode = newNode
        else:
            selNode = self._topNode
            # Emergency while condition, should never happen.
            while selNode.next()!=None:
                if value>selNode.next().value():
                    newNode.setNext(selNode.next())
                    selNode.setNext(newNode)
                elif selNode.next()==None:
                    selNode.setNext(newNode)
                else:
                    selNode = selNode.next()
# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

__author__="Sumner"
__version__="1.0"

class StackNode(object):
    def __init__(self,item,value):
        self.item = item
        self.value = value
        self.nextNode = None
        self.prevNode = None
        
    def setNext(self,nextNode):
        self.nextNode = nextNode
        
    def setPrev(self,prevNode):
        self.prevNode = prevNode
        
    def next(self):
        return self.nextNode
        
    def prev(self):
        return self.prevNode
        
    def getItem(self):
        return self.item

    def getValue(self):
        return self.value

class DataStructure(object):
    '''
    A simple stack which orders by racism severity
    '''
    def __init__(self,maxsize=-1):
        self.maxSize = maxsize
        self.topNode = None
    
    def hasNext(self):
        return self.topNode!=None
    
    def pop(self):
        top = self.topNode
        self.topNode = self.topNode.next()
        return top.getValue()
    
    def add(self,item,value):
        newNode = StackNode(item,value)
        if self.topNode!=None:
            selNode = self.topNode
            while True:
                if value>selNode.getValue():
                    newNode.setPrev(selNode.prev())
                    newNode.setNext(selNode)
                    selNode.prev().setNext(newNode)
                    selNode.setPrev(newNode)
                else:
                    if selNode.next()==None:
                        newNode.setPrev(selNode)
                        selNode.setNext(newNode)
                    else:
                        selNode = selNode.next()
                        break
                    
        else:
            self.topNode=StackNode(item,value)
        self.topNode.setPrev(None)
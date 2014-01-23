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

    def setNext(self,nextNode):
        self.nextNode = nextNode

    def next(self):
        return self.nextNode

    def item(self):
        return self.item

    def value(self):
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
        return top.item()

    def add(self,item,value):
        newNode = StackNode(item,value)
        if self.topNode==None:
            self.topNode = newNode
        elif value>self.topNode.value():
            newNode.setNext(self.topNode)
            self.topNode = newNode
        else:
            selNode = topNode
            # Emergency while condition, should never happen.
            while selNode.next()!=None:
                if value>selNode.next().value():
                    newNode.setNext(selNode.next())
                    selNode.setNext(newNode)
                elif selNode.next()==None:
                    selNode.setNext(newNode)
                else:
                    selNode = selNode.next()

# Uploading this to github
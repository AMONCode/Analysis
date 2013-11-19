"""@package test_classes
Quick test for a class creation. 
"""
class MyClass(object):
    def __init__(self):
        self.test1 = ''
        self.__initialized = True

    def __setattr__(self,name,value):
        if not self.__dict__.has_key('_MyClass__initialized') or self.__dict__.has_key(name):
            object.__setattr__(self, name, value)
        else:
            raise AttributeError("Attribute %s does not exist." % name)

class MyClass2(object):
    __slots__ = ('test1')
    def __init__(self):
        self.test1 = ''


#t = MyClass()
#print
#t.test1 = 'test1_set'
#print t.test1
#print
#t.test2 = 'test2_set'

t = MyClass2()
t.test1 = 'test1_set'
print
print t.test1
print
t.test2 = 'test2_set'

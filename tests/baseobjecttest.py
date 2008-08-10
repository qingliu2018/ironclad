
from tests.utils.runtest import makesuite, run

from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.cpython import MakeTypePtr
from tests.utils.gc import gcwait
from tests.utils.memory import CreateTypes, OffsetPtr
from tests.utils.testcase import TestCase
from tests.utils.typetestcase import TypeTestCase

from System import IntPtr, WeakReference
from System.Runtime.InteropServices import Marshal

from Ironclad import CPyMarshal, CPython_destructor_Delegate, Python25Api, Python25Mapper
from Ironclad.Structs import PyObject, PyTypeObject

    
    
class ObjectFunctionsTest(TestCase):
    
    def testPyObject_Call(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        kallablePtr = mapper.Store(lambda x, y=2: x * y)
        argsPtr = mapper.Store((4,))
        resultPtr = mapper.PyObject_Call(kallablePtr, argsPtr, IntPtr.Zero)
        self.assertEquals(mapper.Retrieve(resultPtr), 8, "didn't call")
        
        kwargsPtr = mapper.Store({'y': 4})
        resultPtr = mapper.PyObject_Call(kallablePtr, argsPtr, kwargsPtr)
        self.assertEquals(mapper.Retrieve(resultPtr), 16, "didn't call with kwargs")
            
        mapper.Dispose()
        deallocTypes()
    
    def testPyObject_Call_noargs(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        kallablePtr = mapper.Store(lambda: 2)
        resultPtr = mapper.PyObject_Call(kallablePtr, IntPtr.Zero, IntPtr.Zero)
        self.assertEquals(mapper.Retrieve(resultPtr), 2, "didn't call")
            
        mapper.Dispose()
        deallocTypes()


    def testPyCallable_Check(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        callables = map(mapper.Store, [float, len, lambda: None])
        notCallables = map(mapper.Store, ["hullo", 33, ])
        
        for x in callables:
            self.assertEquals(mapper.PyCallable_Check(x), 1, "reported not callable")
        for x in notCallables:
            self.assertEquals(mapper.PyCallable_Check(x), 0, "reported callable")
                
        mapper.Dispose()
        deallocTypes()


    def testPyObject_GetAttrString(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        class Thingum(object):
            def __init__(self, bob):
                self.bob = bob
                
        objPtr = mapper.Store(Thingum("Poe"))
        resultPtr = mapper.PyObject_GetAttrString(objPtr, "bob")
        self.assertEquals(mapper.Retrieve(resultPtr), "Poe", "wrong")
            
        mapper.Dispose()
        deallocTypes()


    def testPyObject_GetAttrStringFailure(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        class Thingum(object):
            def __init__(self, bob):
                self.bob = bob
                
        objPtr = mapper.Store(Thingum("Poe"))
        resultPtr = mapper.PyObject_GetAttrString(objPtr, "ben")
        self.assertEquals(resultPtr, IntPtr.Zero, "wrong")
        self.assertEquals(mapper.LastException, None, "no need to set exception, according to spec")
            
        mapper.Dispose()
        deallocTypes()


    def testPyObject_GetAttr(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        class Thingum(object):
            def __init__(self, bob):
                self.bob = bob
                
        objPtr = mapper.Store(Thingum("Poe"))
        resultPtr = mapper.PyObject_GetAttr(objPtr, mapper.Store("bob"))
        self.assertEquals(mapper.Retrieve(resultPtr), "Poe", "wrong")
            
        mapper.Dispose()
        deallocTypes()


    def testPyObject_GetAttrStringFailure(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        class Thingum(object):
            def __init__(self, bob):
                self.bob = bob
                
        objPtr = mapper.Store(Thingum("Poe"))
        resultPtr = mapper.PyObject_GetAttr(objPtr, mapper.Store("ben"))
        self.assertEquals(resultPtr, IntPtr.Zero, "wrong")
        self.assertEquals(mapper.LastException, None, "no need to set exception, assuming this matches GetAttrString")
            
        mapper.Dispose()
        deallocTypes()


    def testPyObject_SetAttrString(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        class C(object):
            pass
        obj = C()
        objPtr = mapper.Store(obj)
        self.assertEquals(mapper.PyObject_SetAttrString(objPtr, "bob", mapper.Store(123)), 0)
        self.assertEquals(obj.bob, 123)
            
        mapper.Dispose()
        deallocTypes()


    def testPyObject_SetAttrString_Failure(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        objPtr = mapper.Store(object())
        self.assertEquals(mapper.PyObject_SetAttrString(objPtr, "bob", mapper.Store(123)), -1)
        def KindaConvertError():
            raise mapper.LastException
        self.assertRaises(AttributeError, KindaConvertError)
            
        mapper.Dispose()
        deallocTypes()


    def testPyObject_SetAttr(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        class C(object):
            pass
        obj = C()
        objPtr = mapper.Store(obj)
        self.assertEquals(mapper.PyObject_SetAttr(objPtr, mapper.Store("bob"), mapper.Store(123)), 0)
        self.assertEquals(obj.bob, 123)
            
        mapper.Dispose()
        deallocTypes()


    def testPyObject_SetAttr_Failure(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        self.assertEquals(mapper.PyObject_SetAttr(mapper.Store(object()), mapper.Store("bob"), mapper.Store(123)), -1)
        def KindaConvertError():
            raise mapper.LastException
        self.assertRaises(AttributeError, KindaConvertError)
            
        mapper.Dispose()
        deallocTypes()


    def testPyObject_HasAttrString(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        class Thingum(object):
            def __init__(self, bob):
                self.bob = bob
                
        objPtr = mapper.Store(Thingum("Poe"))
        self.assertEquals(mapper.PyObject_HasAttrString(objPtr, "bob"), 1)
        self.assertEquals(mapper.PyObject_HasAttrString(objPtr, "jim"), 0)
            
        mapper.Dispose()
        deallocTypes()


    def testPyObject_IsTrue(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        for trueval in ("hullo", 33, -1.5, True, [0], (0,), {1:2}, object()):
            ptr = mapper.Store(trueval)
            self.assertEquals(mapper.PyObject_IsTrue(ptr), 1)
            self.assertEquals(mapper.LastException, None)
            mapper.DecRef(ptr)
        
        for falseval in ('', 0, 0.0, False, [], tuple(), {}):
            ptr = mapper.Store(falseval)
            self.assertEquals(mapper.PyObject_IsTrue(ptr), 0)
            self.assertEquals(mapper.LastException, None)
            mapper.DecRef(ptr)
            
        class MyError(Exception):
            pass
        class ErrorBool(object):
            def __len__(self):
                raise MyError()
        def KindaConvertError():
            raise mapper.LastException
                
        ptr = mapper.Store(ErrorBool())
        self.assertEquals(mapper.PyObject_IsTrue(ptr), -1)
        self.assertRaises(MyError, KindaConvertError)
        mapper.DecRef(ptr)
        
        mapper.Dispose()
        deallocTypes()


    def testPyObject_Size(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        for okval in ("hullo", [0, 3, 5], (0,), {1:2}, set([1, 2])):
            ptr = mapper.Store(okval)
            self.assertEquals(mapper.PyObject_Size(ptr), len(okval))
            self.assertEquals(mapper.LastException, None)
            mapper.DecRef(ptr)
        
        for badval in (0, 0.0, False, object, object()):
            ptr = mapper.Store(badval)
            self.assertEquals(mapper.PyObject_Size(ptr), -1)
            def KindaConvertError():
                raise mapper.LastException
            self.assertRaises(TypeError, KindaConvertError)
            mapper.DecRef(ptr)
            
        mapper.Dispose()
        deallocTypes()


    def testPyObject_Str(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        for okval in ("hullo", [0, 3, 5], (0,), {1:2}, set([1, 2])):
            ptr = mapper.Store(okval)
            strptr = mapper.PyObject_Str(ptr)
            self.assertEquals(mapper.Retrieve(strptr), str(okval))
            self.assertEquals(mapper.LastException, None)
            mapper.DecRef(ptr)
            mapper.DecRef(strptr)
        
        class BadStr(object):
            def __str__(self):
                raise TypeError('this object cannot be represented in your puny alphabet')
        
        ptr = mapper.Store(BadStr())
        self.assertEquals(mapper.PyObject_Str(ptr), IntPtr.Zero)
        def KindaConvertError():
            raise mapper.LastException
        self.assertRaises(TypeError, KindaConvertError)
        mapper.DecRef(ptr)
            
        mapper.Dispose()
        deallocTypes()
        

class IterationTest(TestCase):
    
    def testPyObject_GetIter_Success(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        testList = [1, 2, 3]
        listPtr = mapper.Store(testList)
        iterPtr = mapper.PyObject_GetIter(listPtr)
        iter = mapper.Retrieve(iterPtr)
        self.assertEquals([x for x in iter], testList, "bad iterator")
            
        mapper.Dispose()
        deallocTypes()
    
    
    def testPyObject_GetIter_Failure(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        testObj = object()
        objPtr = mapper.Store(testObj)
        iterPtr = mapper.PyObject_GetIter(objPtr)
        self.assertEquals(iterPtr, IntPtr.Zero, "returned iterator inappropriately")
        self.assertNotEquals(mapper.LastException, None, "failed to set exception")
        
        def Raise():
            raise mapper.LastException
        try:
            Raise()
        except TypeError, e:
            self.assertEquals(str(e), "PyObject_GetIter: object is not iterable", "bad message")
        else:
            self.fail("wrong exception")
                
        mapper.Dispose()
        deallocTypes()
    
    
    def testPyIter_Next_Success(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        testList = [0, 1, 2]
        listPtr = mapper.Store(testList)
        iterPtr = mapper.PyObject_GetIter(listPtr)
        
        for i in range(3):
            itemPtr = mapper.PyIter_Next(iterPtr)
            self.assertEquals(mapper.Retrieve(itemPtr), i, "got wrong object back")
            self.assertEquals(mapper.RefCount(itemPtr), 2, "failed to incref")
            mapper.DecRef(itemPtr)
        
        noItemPtr = mapper.PyIter_Next(iterPtr)
        self.assertEquals(noItemPtr, IntPtr.Zero, "failed to stop iterating")
            
        mapper.Dispose()
        deallocTypes()
    
    
    def testPyIter_Next_NotAnIterator(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        notIterPtr = mapper.Store(object())
        self.assertEquals(mapper.PyIter_Next(notIterPtr), IntPtr.Zero, "bad return")
        self.assertNotEquals(mapper.LastException, None, "failed to set exception")
        
        def Raise():
            raise mapper.LastException
        try:
            Raise()
        except TypeError, e:
            self.assertEquals(str(e), "PyIter_Next: object is not an iterator", "bad message")
        else:
            self.fail("wrong exception")
            
        mapper.Dispose()
        deallocTypes()
    
    
    def testPyIter_Next_ExplodingIterator(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        class BorkedException(Exception):
            pass
        def GetNext():
            raise BorkedException("Release the hounds!")
        explodingIterator = (GetNext() for _ in range(3))
        
        iterPtr = mapper.Store(explodingIterator)
        self.assertEquals(mapper.PyIter_Next(iterPtr), IntPtr.Zero, "bad return")
        self.assertNotEquals(mapper.LastException, None, "failed to set exception")
        
        def Raise():
            raise mapper.LastException
        try:
            Raise()
        except BorkedException, e:
            self.assertEquals(str(e), "Release the hounds!", "unexpected message")
        else:
            self.fail("wrong exception")
            
        mapper.Dispose()
        deallocTypes()
    
    
class PyBaseObject_Type_Test(TypeTestCase):

    def testPyBaseObject_Type_fields(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        def AssertPtrField(name, value):
            field = CPyMarshal.ReadPtrField(mapper.PyBaseObject_Type, PyTypeObject, name)
            self.assertNotEquals(field, IntPtr.Zero)
            self.assertEquals(field, value)
        
        AssertPtrField("tp_init", mapper.GetAddress("PyBaseObject_Init"))
        AssertPtrField("tp_alloc", mapper.GetAddress("PyType_GenericAlloc"))
        AssertPtrField("tp_new", mapper.GetAddress("PyType_GenericNew"))
        
        mapper.Dispose()
        deallocTypes()


    def testPyBaseObject_Type_tp_dealloc(self):
        self.assertUsual_tp_dealloc("PyBaseObject_Type")


    def testPyBaseObject_Type_tp_free(self):
        self.assertUsual_tp_free("PyBaseObject_Type")
            
    
    def testPyBaseObject_TypeDeallocCallsObjTypesFreeFunction(self):
        calls = []
        def Some_FreeFunc(objPtr):
            calls.append(objPtr)
        self.freeDgt = Python25Api.PyObject_Free_Delegate(Some_FreeFunc)
        
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        baseObjTypeBlock = mapper.PyBaseObject_Type
        objTypeBlock = mapper.PyDict_Type # type not actually important
        objPtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        
        CPyMarshal.WriteFunctionPtrField(objTypeBlock, PyTypeObject, "tp_free", self.freeDgt)
        CPyMarshal.WritePtrField(objPtr, PyObject, "ob_type", objTypeBlock)
        gcwait() # this should make the function pointers invalid if we forgot to store references to the delegates

        mapper.PyBaseObject_Dealloc(objPtr)
        self.assertEquals(calls, [objPtr], "wrong calls")
            
        mapper.Dispose()
        deallocTypes()
        Marshal.FreeHGlobal(objPtr)


class NewInitFunctionsTest(TestCase):
    
    def testPyObject_Init(self):
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        typePtr, deallocType = MakeTypePtr(mapper, {'tp_name': 'FooType'})
        objPtr = Marshal.AllocHGlobal(Marshal.SizeOf(PyObject))
        
        self.assertEquals(mapper.PyObject_Init(objPtr, typePtr), objPtr, 'did not return the "new instance"')
        self.assertEquals(CPyMarshal.ReadPtrField(objPtr, PyObject, "ob_type"), typePtr, "wrong type")
        self.assertEquals(CPyMarshal.ReadIntField(objPtr, PyObject, "ob_refcnt"), 1, "wrong refcount")
        self.assertEquals(mapper.HasPtr(objPtr), False)
        
        mapper.Dispose()
        Marshal.FreeHGlobal(objPtr)
        deallocType()
        deallocTypes()


    def testPyBaseObject_Init(self):
        "this function shouldn't do anything..."
        mapper = Python25Mapper()
        deallocTypes = CreateTypes(mapper)
        
        self.assertEquals(mapper.PyBaseObject_Init(IntPtr.Zero, IntPtr.Zero, IntPtr.Zero), 0)
        
        mapper.Dispose()
        deallocTypes()
    
    
    def test_PyObject_New(self):
        allocs = []
        allocator = GetAllocatingTestAllocator(allocs, [])
        mapper = Python25Mapper(allocator)
        deallocTypes = CreateTypes(mapper)
        
        typeObjSize = Marshal.SizeOf(PyTypeObject)
        typePtr = Marshal.AllocHGlobal(typeObjSize)
        CPyMarshal.Zero(typePtr, typeObjSize)
        CPyMarshal.WriteIntField(typePtr, PyTypeObject, "ob_size", 31337)
        
        del allocs[:]
        objPtr = mapper._PyObject_New(typePtr)
        self.assertEquals(allocs, [(objPtr, 31337)])
        self.assertEquals(CPyMarshal.ReadPtrField(objPtr, PyObject, 'ob_type'), typePtr)
        self.assertEquals(CPyMarshal.ReadIntField(objPtr, PyObject, 'ob_refcnt'), 1)
        self.assertEquals(mapper.HasPtr(objPtr), False)
        
        mapper.Dispose()
        deallocTypes()
        

suite = makesuite(
    ObjectFunctionsTest,
    IterationTest,
    PyBaseObject_Type_Test,
    NewInitFunctionsTest,
)

if __name__ == '__main__':
    run(suite)

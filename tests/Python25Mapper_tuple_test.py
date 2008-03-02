
import unittest
from tests.utils.allocators import GetAllocatingTestAllocator
from tests.utils.memory import OffsetPtr
from tests.utils.runtest import makesuite, run

from System import GC, IntPtr
from System.Runtime.InteropServices import Marshal

from IronPython.Hosting import PythonEngine
from Ironclad import CPyMarshal, CPython_destructor_Delegate, Python25Mapper
from Ironclad.Structs import PyTupleObject, PyTypeObject

class Python25Mapper_Tuple_Test(unittest.TestCase):
    
    def assertPyTuple_New_Works(self, length):
        allocs = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, []))

        typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        try:
            mapper.SetData("PyTuple_Type", typeBlock)
            tuplePtr = mapper.PyTuple_New(length)
            try:
                expectedSize = Marshal.SizeOf(PyTupleObject) + (CPyMarshal.PtrSize * (length - 1))
                self.assertEquals(allocs, [(tuplePtr, expectedSize)], "bad alloc")
                tupleStruct = Marshal.PtrToStructure(tuplePtr, PyTupleObject)
                self.assertEquals(tupleStruct.ob_refcnt, 1, "bad refcount")
                self.assertEquals(tupleStruct.ob_type, mapper.PyTuple_Type, "bad type")
                self.assertEquals(tupleStruct.ob_size, length, "bad size")
                dataPtr = OffsetPtr(tuplePtr, Marshal.OffsetOf(PyTupleObject, "ob_item"))
                itemPtrs = []
                for i in range(length):
                    itemPtr = mapper.Store(i + 100)
                    CPyMarshal.WritePtr(dataPtr, itemPtr)
                    itemPtrs.append(itemPtr)
                    dataPtr = OffsetPtr(dataPtr, CPyMarshal.PtrSize)
                    
                immutableTuple = mapper.Retrieve(tuplePtr)
                self.assertEquals(immutableTuple, tuple(i + 100 for i in range(length)), "broken")
            finally:
                mapper.DecRef(tuplePtr)
        finally:
            Marshal.FreeHGlobal(typeBlock)
    
    
    def testPyTuple_New(self):
        self.assertPyTuple_New_Works(1)
        self.assertPyTuple_New_Works(3)


    def testPyTupleTypeField_tp_dealloc(self):
        calls = []
        class MyPM(Python25Mapper):
            def PyTuple_Dealloc(self, tuplePtr):
                calls.append(tuplePtr)
        
        engine = PythonEngine()
        mapper = MyPM(engine)
        
        typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        try:
            mapper.SetData("PyTuple_Type", typeBlock)
            GC.Collect() # this will make the function pointers invalid if we forgot to store references to the delegates

            deallocFPPtr = OffsetPtr(typeBlock, Marshal.OffsetOf(PyTypeObject, "tp_dealloc"))
            deallocFP = CPyMarshal.ReadPtr(deallocFPPtr)
            deallocDgt = Marshal.GetDelegateForFunctionPointer(deallocFP, CPython_destructor_Delegate)
            deallocDgt(IntPtr(12345))
            self.assertEquals(calls, [IntPtr(12345)], "wrong calls")
        finally:
            Marshal.FreeHGlobal(typeBlock)


    def testPyTupleTypeField_tp_free(self):
        calls = []
        class MyPM(Python25Mapper):
            def Free(self, tuplePtr):
                calls.append(tuplePtr)
        
        engine = PythonEngine()
        mapper = MyPM(engine)
        
        typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        try:
            mapper.SetData("PyTuple_Type", typeBlock)
            GC.Collect() # this will make the function pointers invalid if we forgot to store references to the delegates

            freeFPPtr = OffsetPtr(typeBlock, Marshal.OffsetOf(PyTypeObject, "tp_free"))
            freeFP = CPyMarshal.ReadPtr(freeFPPtr)
            freeDgt = Marshal.GetDelegateForFunctionPointer(freeFP, CPython_destructor_Delegate)
            freeDgt(IntPtr(12345))
            self.assertEquals(calls, [IntPtr(12345)], "wrong calls")
        finally:
            Marshal.FreeHGlobal(typeBlock)


    def makeTuple(self, mapper, model):
        tuplePtr = mapper.PyTuple_New(len(model))
        dataPtr = OffsetPtr(tuplePtr, Marshal.OffsetOf(PyTupleObject, "ob_item"))
        itemPtrs = []
        for i in range(len(model)):
            itemPtr = mapper.Store(model[i])
            itemPtrs.append(itemPtr)
            CPyMarshal.WritePtr(dataPtr, itemPtr)
            dataPtr = OffsetPtr(dataPtr, CPyMarshal.PtrSize)
        return tuplePtr, itemPtrs
        

    def testPyTuple_DeallocDecRefsItemsAndCallsCorrectFreeFunction(self):
        frees = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator([], frees))
        
        calls = []
        def CustomFree(ptr):
            calls.append(ptr)
        freeDgt = CPython_destructor_Delegate(CustomFree)
        freeFP = Marshal.GetFunctionPointerForDelegate(freeDgt)
        
        typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        try:
            mapper.SetData("PyTuple_Type", typeBlock)
            freeFPPtr = OffsetPtr(typeBlock, Marshal.OffsetOf(PyTypeObject, "tp_free"))
            CPyMarshal.WritePtr(freeFPPtr, freeFP)
            tuplePtr, itemPtrs = self.makeTuple(mapper, (1, 2, 3))
            
            mapper.PyTuple_Dealloc(tuplePtr)
            
            for itemPtr in itemPtrs:
                self.assertEquals(itemPtr in frees, True, "did not decref item")
                self.assertEquals(mapper.RefCount(itemPtr), 0, "did not decref item")
            self.assertEquals(calls, [tuplePtr], "did not call type's free function")
            mapper.Free(tuplePtr)
        finally:
            Marshal.FreeHGlobal(typeBlock)


    def testStoreTupleCreatesTupleType(self):
        allocs = []
        engine = PythonEngine()
        mapper = Python25Mapper(engine, GetAllocatingTestAllocator(allocs, []))
        
        typeBlock = Marshal.AllocHGlobal(Marshal.SizeOf(PyTypeObject))
        try:
            mapper.SetData("PyTuple_Type", typeBlock)
            tuplePtr = mapper.Store((0, 1, 2))
            try:
                ob_typePtr = OffsetPtr(tuplePtr, Marshal.OffsetOf(PyTupleObject, "ob_type"))
                self.assertEquals(CPyMarshal.ReadPtr(ob_typePtr), typeBlock, "wrong type")
                
                dataPtr = OffsetPtr(tuplePtr, Marshal.OffsetOf(PyTupleObject, "ob_item"))
                for i in range(3):
                    item = mapper.Retrieve(CPyMarshal.ReadPtr(dataPtr))
                    self.assertEquals(item, i, "did not store data")
                    dataPtr = OffsetPtr(dataPtr, CPyMarshal.PtrSize)
                
            finally:
                mapper.DecRef(tuplePtr)
        finally:
            Marshal.FreeHGlobal(typeBlock)
        
        



suite = makesuite(
    Python25Mapper_Tuple_Test,
)

if __name__ == '__main__':
    run(suite)
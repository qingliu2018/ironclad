
import os
import unittest
from tests.utils.memory import ptrSize, OffsetPtr

from System import IntPtr
from System.Runtime.InteropServices import Marshal

from JumPy import AddressGetterDelegate, DataSetterDelegate, PythonMapper, StubReference

from JumPyTestUtils import PythonStubHarness


class PyArg_ParseTupleAndKeywordsTest(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        test = self
        class MyPM(PythonMapper):
            def PyArg_ParseTupleAndKeywords(self, args, kwargs, format, kwlist, argptr):
                test.assertMatchesVargargs((args, kwargs, format, kwlist, argptr))
                return 1

        self.sr = StubReference(os.path.join("build", "python25.dll"))
        self.pm = MyPM()
        self.sr.Init(AddressGetterDelegate(self.pm.GetAddress), DataSetterDelegate(self.pm.SetData))


    def tearDown(self):
        self.sr.Dispose()
        del self.pm


    def assertMatchesVargargs(self, params):
        self.assertEquals(params[:4], (IntPtr(1), IntPtr(2), "i" * len(self.varargs), IntPtr(3)),
                          "error marshalling easy args")

        argPtr = params[4]
        for i, ptr in enumerate(self.varargs):
            thisArgAddressPtr = OffsetPtr(argPtr, ptrSize * i)
            thisArgAddress = Marshal.ReadIntPtr(thisArgAddressPtr)
            self.assertEquals(thisArgAddress, ptr, "error marshalling varargs")


    def assertMarshalsVarargs(self, varargs):
        testFuncName = "Test_PA_PTAK__%darg" % len(varargs)
        testFunc = getattr(PythonStubHarness, testFuncName)
        self.varargs = varargs
        result = testFunc(IntPtr(1), IntPtr(2), "i" * len(varargs), IntPtr(3), *varargs)
        self.assertEquals(result, 1, "bad return value")


    def test1Arg(self):
        self.assertMarshalsVarargs((IntPtr(100),))


    def test2Args(self):
        self.assertMarshalsVarargs((IntPtr(100), IntPtr(200)))


    def test3Args(self):
        self.assertMarshalsVarargs((IntPtr(100), IntPtr(200), IntPtr(300)))



suite = unittest.TestSuite()
loader = unittest.TestLoader()
suite.addTest(loader.loadTestsFromTestCase(PyArg_ParseTupleAndKeywordsTest))

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)
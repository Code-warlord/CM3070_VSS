if(EXISTS "C:/test/VSS_python_cpp_wrapper/py_subsense_module/subsense_python_wrapper/test/build_win/runTests[1]_tests.cmake")
  include("C:/test/VSS_python_cpp_wrapper/py_subsense_module/subsense_python_wrapper/test/build_win/runTests[1]_tests.cmake")
else()
  add_test(runTests_NOT_BUILT runTests_NOT_BUILT)
endif()

cmake_minimum_required(VERSION 3.15)
project(Test_Subsense_Python_Wrapper)

set(CMAKE_CXX_STANDARD 14)

# Get parent directories (adjust as needed for your project structure)
get_filename_component(LVL_1_DIR_ABOVE_CMAKE_SOURCE_DIR ${PROJECT_SOURCE_DIR} DIRECTORY)
get_filename_component(LVL_2_DIR_ABOVE_CMAKE_SOURCE_DIR ${LVL_1_DIR_ABOVE_CMAKE_SOURCE_DIR} DIRECTORY)

# Set Python executable based on OS.
if(WIN32)
    set(Python_EXECUTABLE "C:/compilers/python3_12_8/python.exe")
elseif(UNIX)
    set(Python_EXECUTABLE "/usr/local/bin/python3.12")
else()
    message(FATAL_ERROR "Unsupported operating system: ${CMAKE_SYSTEM_NAME}")
endif()

# Find Python development components.
find_package(Python REQUIRED COMPONENTS Interpreter Development)
if (NOT Python_FOUND)
    message(FATAL_ERROR "Python development environment not found. Ensure Python is installed with headers and libraries.")
endif()

# Debug output for Python paths.
message(STATUS "Python version: ${Python_VERSION}")
message(STATUS "Python include dirs: ${Python_INCLUDE_DIRS}")
message(STATUS "Python libraries: ${Python_LIBRARIES}")

# Instruct pybind11 to use modern Python finding.
set(PYBIND11_FINDPYTHON ON)

# Set CMAKE_PREFIX_PATH for pybind11 and OpenCV based on OS.
if(WIN32)
    list(APPEND CMAKE_PREFIX_PATH "C:/compilers/python3_12_8/Lib/site-packages/pybind11/share/cmake/pybind11")
    list(APPEND CMAKE_PREFIX_PATH "C:/compilers/Cpp_Libraries/opencv/build")
elseif(UNIX)
    list(APPEND CMAKE_PREFIX_PATH "/usr/local/lib/python3.12/site-packages/pybind11/share/cmake/pybind11")
    list(APPEND CMAKE_PREFIX_PATH "/usr/local/lib/cmake/opencv4")
endif()

# Find OpenCV and pybind11.
find_package(OpenCV REQUIRED)
find_package(pybind11 REQUIRED)

message(STATUS "Linked OpenCV libraries: ${OpenCV_LIBS}")

# Add your source code library.
add_library(test_subsense 
    ${LVL_2_DIR_ABOVE_CMAKE_SOURCE_DIR}/external/cpp/subsense_by_Pierre_Luc_St_Charles_et_al/BackgroundSubtractorLBSP.cpp
    ${LVL_2_DIR_ABOVE_CMAKE_SOURCE_DIR}/external/cpp/subsense_by_Pierre_Luc_St_Charles_et_al/BackgroundSubtractorSuBSENSE.cpp
    ${LVL_2_DIR_ABOVE_CMAKE_SOURCE_DIR}/external/cpp/subsense_by_Pierre_Luc_St_Charles_et_al/LBSP.cpp
    ${LVL_1_DIR_ABOVE_CMAKE_SOURCE_DIR}/BackgroundSubtractorSubsensePythonWrapper.cpp
)

target_include_directories(test_subsense PUBLIC 
    ${LVL_1_DIR_ABOVE_CMAKE_SOURCE_DIR}
    ${LVL_2_DIR_ABOVE_CMAKE_SOURCE_DIR}/external/cpp/subsense_by_Pierre_Luc_St_Charles_et_al
)

# Link your library with OpenCV, pybind11, and Python libraries.
target_link_libraries(test_subsense PUBLIC ${OpenCV_LIBS} pybind11::module ${Python_LIBRARIES})

set(GOOGLETEST_VERSION "1.16.0")  # Use the version you downloaded

# Enable testing so that CTest can discover tests.
enable_testing()

# Include GoogleTest manually by adding its directory.
add_subdirectory("external/googletest")

# Add the test executable.
add_executable(runTests test_BackgroundSubtractorSubsensePythonWrapper.cpp)
target_link_libraries(runTests PRIVATE test_subsense gtest_main pybind11::module ${Python_LIBRARIES})

include(GoogleTest)
gtest_discover_tests(runTests)









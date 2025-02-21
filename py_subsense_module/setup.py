
from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext
import platform
from pathlib import Path
import shutil

# Determine OS and set OpenCV paths and libraries.
if platform.system() == "Windows":
    opencv_include = str(Path("C:/compilers/Cpp_Libraries/opencv/build/include").resolve())
    opencv_lib = str(Path("C:/compilers/Cpp_Libraries/opencv/build/x64/vc16/lib").resolve())
    opencv_dll = str(Path("C:/compilers/Cpp_Libraries/opencv/build/x64/vc16/bin").resolve())
    opencv_libs = ["opencv_world4100"]
    # We'll copy the DLL from the OpenCV library directory during build.
    dll_filename = "opencv_world4100.dll"
else:
    # Linux settings.
    opencv_include = str(Path("/usr/local/include/opencv4").resolve())
    opencv_lib = str(Path("/usr/local/lib").resolve())
    opencv_libs = [
        "opencv_imgproc",
        "opencv_calib3d",
        "opencv_ml",
        "opencv_core",
        "opencv_objdetect",
        "opencv_dnn",
        "opencv_photo",
        "opencv_features2d",
        "opencv_stitching",
        "opencv_flann",
        "opencv_videoio",
        "opencv_gapi",
        "opencv_video",
        "opencv_highgui",
        "opencv_imgcodecs",
    ]
    dll_filename = None  # Not used on Linux

# Custom build_ext to copy DLL for Windows.
class custom_build_ext(build_ext):
    def run(self):
        build_ext.run(self)
        if platform.system() == "Windows" and dll_filename:
            src_dll = Path(opencv_dll) / dll_filename
            # Determine destination folder. For wheel builds, self.build_lib is the temporary build directory.
            dest_dll = Path(self.build_lib) / "pysubsense" / dll_filename
            print(f"Copying {src_dll} to {dest_dll}")
            try:
                shutil.copy(str(src_dll), str(dest_dll))
            except Exception as e:
                raise RuntimeError(f"Failed to copy DLL from {src_dll} to {dest_dll}: {e}")

ext_modules = [
    Pybind11Extension(
        "pysubsense.subsense",
        [
            "external/cpp/subsense_by_Pierre_Luc_St_Charles_et_al/BackgroundSubtractorLBSP.cpp",
            "external/cpp/subsense_by_Pierre_Luc_St_Charles_et_al/LBSP.cpp",
            "external/cpp/subsense_by_Pierre_Luc_St_Charles_et_al/BackgroundSubtractorSuBSENSE.cpp",
            "subsense_python_wrapper/BackgroundSubtractorSubsensePythonWrapper.cpp",
        ],
        include_dirs=[
            "external/cpp/subsense_by_Pierre_Luc_St_Charles_et_al",
            "subsense_python_wrapper",
            opencv_include,
        ],
        libraries=opencv_libs,
        library_dirs=[opencv_lib],
        cxx_std=14,
    ),
]

# On Linux, we don't need to include any extra DLLs in data_files.
# On Windows, since we are copying the DLL at build time, we omit data_files.
data_files = []  

setup(
    name="pysubsense",
    version="0.1.0",
    author="Victor ogbogolo",
    description="Subsense Python Wrapper using pybind11",
    ext_modules=ext_modules,
    cmdclass={"build_ext": custom_build_ext},
    zip_safe=False,
    python_requires=">=3.12",
    packages=["pysubsense"],
    data_files=data_files,
    include_package_data=True,
)

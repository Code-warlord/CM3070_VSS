#ifndef BACKGROUNDSUBTRACTORSUBSENSEPYTHONWRAPPER_H
#define BACKGROUNDSUBTRACTORSUBSENSEPYTHONWRAPPER_H

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <opencv2/opencv.hpp>

namespace py = pybind11;

// Converts a numpy array to a cv::Mat.
// Throws a runtime error if the input does not have 2 or 3 dimensions.
cv::Mat numpy_to_mat(py::array_t<unsigned char>& input);

// Converts a cv::Mat to a numpy array.
// Throws a runtime error if the input cv::Mat is empty.
py::array_t<unsigned char> mat_to_numpy(const cv::Mat &mat);

#endif // BACKGROUNDSUBTRACTORSUBSENSEPYTHONWRAPPER_H

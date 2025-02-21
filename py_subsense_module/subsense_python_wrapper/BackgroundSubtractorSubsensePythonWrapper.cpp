#include <stdexcept>
#include <vector>
#include "BackgroundSubtractorSubsensePythonWrapper.h"
#include "BackgroundSubtractorSuBSENSE.h" // this header is from subsense_by_Pierre_Luc_St_Charles_et_al available in cmake include path


cv::Mat numpy_to_mat(py::array_t<unsigned char> &input)
{
    py::buffer_info buf = input.request();
    if (buf.ndim != 2 && buf.ndim != 3)
    {
        throw std::runtime_error("Input numpy array must have 2 or 3 dimensions.");
    }
    // If the input is 3-dimensional, enforce that there are exactly 3 channels.
    if (buf.ndim == 3 && buf.shape[2] != 3)
    {
        throw std::runtime_error("Input numpy array must have 3 channels when 3-dimensional.");
    }

    int rows = static_cast<int>(buf.shape[0]);
    int cols = static_cast<int>(buf.shape[1]);
    int channels = (buf.ndim == 3) ? static_cast<int>(buf.shape[2]) : 1;

    // Create a cv::Mat that shares data with the numpy array, then clone it to ensure ownership.
    cv::Mat mat(rows, cols, CV_8UC(channels), reinterpret_cast<unsigned char *>(buf.ptr));
    return mat.clone();
}

py::array_t<unsigned char> mat_to_numpy(const cv::Mat &mat)
{
    if (mat.empty())
    {
        throw std::runtime_error("Input cv::Mat is empty");
    }

    // Allow only 2D matrices (OpenCV standard for images).
    if (mat.dims != 2)
    {
        throw std::runtime_error("Input cv::Mat must be 2-dimensional.");
    }

    std::vector<size_t> shape;
    std::vector<size_t> strides;

    // For 2D Mat, include channels as the third dimension if > 1.
    shape.push_back(static_cast<size_t>(mat.rows));
    shape.push_back(static_cast<size_t>(mat.cols));

    const int channels = mat.channels();
    if (channels > 1)
    {
        shape.push_back(static_cast<size_t>(channels));
    }

    // Strides in bytes: OpenCV uses contiguous row-major order by default.
    strides.push_back(static_cast<size_t>(mat.step[0])); // Row stride
    strides.push_back(static_cast<size_t>(mat.step[1])); // Column stride (bytes per element × channels)
    if (channels > 1)
    {
        strides.push_back(static_cast<size_t>(mat.elemSize1())); // Channel stride
    }

    return py::array_t<unsigned char>(
        shape,
        strides,
        mat.data);
}

// This block defines the Python module `subsense` using pybind11, which wraps the BackgroundSubtractorSuBSENSE class for Python interaction.
// The module provides bindings for background subtraction algorithms to be used directly from Python.
PYBIND11_MODULE(subsense, m)
{
    // This defines the BackgroundSubtractorSuBSENSE class in Python. The class provides advanced background subtraction capabilities.
    // It is particularly useful in video analysis and processing tasks where detecting moving objects is critical.
    py::class_<BackgroundSubtractorSuBSENSE>(m, "BackgroundSubtractorSuBSENSE")
        .def(py::init<float, size_t, size_t, size_t, size_t, size_t>(),
             py::arg("fRelLBSPThreshold") = BGSSUBSENSE_DEFAULT_LBSP_REL_SIMILARITY_THRESHOLD,
             py::arg("nDescDistThresholdOffset") = BGSSUBSENSE_DEFAULT_DESC_DIST_THRESHOLD_OFFSET,
             py::arg("nMinColorDistThreshold") = BGSSUBSENSE_DEFAULT_MIN_COLOR_DIST_THRESHOLD,
             py::arg("nBGSamples") = BGSSUBSENSE_DEFAULT_NB_BG_SAMPLES,
             py::arg("nRequiredBGSamples") = BGSSUBSENSE_DEFAULT_REQUIRED_NB_BG_SAMPLES,
             py::arg("nSamplesForMovingAvgs") = BGSSUBSENSE_DEFAULT_N_SAMPLES_FOR_MV_AVGS)
        .def("initialize", [](BackgroundSubtractorSuBSENSE &self, py::array_t<unsigned char> oInitImg, py::array_t<unsigned char> oROI)
             {
                // Convert the input numpy arrays to cv::Mat objects
                cv::Mat initImg = numpy_to_mat(oInitImg);
                cv::Mat roi = numpy_to_mat(oROI);
                
                // Initialize the background subtractor with the provided initial image and region of interest (ROI)
                // The initial image should be a grayscale or color image representing the background, and the ROI
                // should be a binary mask indicating the region of interest for background subtraction.
                // Ensure that the dimensions of the ROI match those of the initial image to avoid runtime errors.
                self.initialize(initImg, roi); }, 
                py::arg("oInitImg"), 
                py::arg("oROI"), 
                "Initialize the background subtractor with an initial image and ROI.")
        .def("apply", [](BackgroundSubtractorSuBSENSE &self, py::array_t<unsigned char> image, double learningRateOverride)
             {
                cv::Mat inputMat = numpy_to_mat(image);
                cv::Mat fgmask;
                // Apply the background subtraction algorithm on the input image.
                // The learningRateOverride parameter determines the rate at which the background model is updated.
                // A value of 0 keeps the model unchanged, while higher values update the model faster.
                self.apply(inputMat, fgmask, learningRateOverride);
                return mat_to_numpy(fgmask); }, 
                py::arg("image"), 
                py::arg("learningRateOverride") = 0.0, 
                "Apply the background subtraction algorithm and return the foreground mask.")
        .def("getBackgroundImage", [](BackgroundSubtractorSuBSENSE &self)
             {
                cv::Mat backgroundImage;
                self.getBackgroundImage(backgroundImage);
                // This method retrieves the reconstructed background image.
                // It is particularly useful in scenarios where the static background needs to be analyzed or visualized,
                // such as monitoring changes over time in a scene or identifying stationary objects.
                return mat_to_numpy(backgroundImage); }, "Retrieve the reconstructed background image.");
}
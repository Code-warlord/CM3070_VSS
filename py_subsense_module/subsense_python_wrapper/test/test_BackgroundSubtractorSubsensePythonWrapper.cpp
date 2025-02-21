#include <gtest/gtest.h>
#include <pybind11/embed.h> // For py::scoped_interpreter
#include <pybind11/numpy.h>
#include <opencv2/opencv.hpp>
#include <stdexcept>
#include <vector>
#include "BackgroundSubtractorSubsensePythonWrapper.h" // Assumes this header declares numpy_to_mat

namespace py = pybind11;


// Base test fixture for Python interpreter setup/teardown
class PythonInterpreterFixture : public ::testing::Test
{
protected:
    static py::scoped_interpreter *guard;

    static void SetUpTestSuite()
    {
        if (!guard)
        {
            guard = new py::scoped_interpreter{};
        }
    }

    static void TearDownTestSuite()
    {
        delete guard;
        guard = nullptr;
    }
};

py::scoped_interpreter *PythonInterpreterFixture::guard = nullptr;

// Fixture for numpy_to_mat tests
class NumpyToMatTest : public PythonInterpreterFixture
{
};

// Fixture for mat_to_numpy tests
class MatToNumpyTest : public PythonInterpreterFixture
{
};

// Test normal condition: valid 2D (grayscale) array.
TEST_F(NumpyToMatTest, Grayscale2DValidInput)
{
    // Create a 2D numpy array of shape (5, 4)
    const int rows = 5, cols = 4;
    std::vector<unsigned char> data(rows * cols);
    // Fill with sequential values for verification.
    for (int i = 0; i < rows * cols; i++)
    {
        data[i] = static_cast<unsigned char>(i);
    }

    auto np_array = py::array_t<unsigned char>(
        {rows, cols},
        {cols * sizeof(unsigned char), sizeof(unsigned char)},
        data.data());

    // Call the conversion function.
    cv::Mat mat = numpy_to_mat(np_array);

    // Verify dimensions: should be rows x cols with 1 channel.
    EXPECT_EQ(mat.rows, rows);
    EXPECT_EQ(mat.cols, cols);
    EXPECT_EQ(mat.channels(), 1);

    // Check each pixel value.
    for (int i = 0; i < mat.rows; i++)
    {
        for (int j = 0; j < mat.cols; j++)
        {
            EXPECT_EQ(mat.at<unsigned char>(i, j), data[i * cols + j]);
        }
    }
}

// Test normal condition: valid 3D (color) array.
TEST_F(NumpyToMatTest, Color3DValidInput)
{
    // Create a 3D numpy array with shape (3, 4, 3)
    const int rows = 3, cols = 4, channels = 3;
    std::vector<unsigned char> data(rows * cols * channels);
    // Fill with a pattern: for each pixel, value = row*10 + col (for all channels).
    for (int i = 0; i < rows; i++)
    {
        for (int j = 0; j < cols; j++)
        {
            for (int c = 0; c < channels; c++)
            {
                data[(i * cols + j) * channels + c] = static_cast<unsigned char>(i * 10 + j);
            }
        }
    }

    auto np_array = py::array_t<unsigned char>(
        {rows, cols, channels},
        {cols * channels * sizeof(unsigned char),
         channels * sizeof(unsigned char),
         sizeof(unsigned char)},
        data.data());

    cv::Mat mat = numpy_to_mat(np_array);

    EXPECT_EQ(mat.rows, rows);
    EXPECT_EQ(mat.cols, cols);
    EXPECT_EQ(mat.channels(), channels);

    // Check each pixel value.
    for (int i = 0; i < mat.rows; i++)
    {
        for (int j = 0; j < mat.cols; j++)
        {
            cv::Vec3b pixel = mat.at<cv::Vec3b>(i, j);
            for (int c = 0; c < channels; c++)
            {
                EXPECT_EQ(pixel[c], data[(i * cols + j) * channels + c]);
            }
        }
    }
}

// Test boundary condition: invalid number of dimensions (e.g., 1D array).
TEST_F(NumpyToMatTest, InvalidDimensionsThrows)
{
    // Create a 1D numpy array (shape: [10]), which is invalid.
    const int size = 10;
    std::vector<unsigned char> data(size, 0);
    auto np_array = py::array_t<unsigned char>(
        {size},
        {sizeof(unsigned char)},
        data.data());

    EXPECT_THROW({ numpy_to_mat(np_array); }, std::runtime_error);
}

// Test boundary condition: 3D array with incorrect channel count (e.g., 2 channels).
TEST_F(NumpyToMatTest, ThreeDimWrongChannelsThrows)
{
    // Create a 3D numpy array with shape (5, 5, 2) which is invalid for a color image.
    const int rows = 5, cols = 5, channels = 2;
    std::vector<unsigned char> data(rows * cols * channels, 0);
    auto np_array = py::array_t<unsigned char>(
        {rows, cols, channels},
        {cols * channels * sizeof(unsigned char),
         channels * sizeof(unsigned char),
         sizeof(unsigned char)},
        data.data());

    EXPECT_THROW({ numpy_to_mat(np_array); }, std::runtime_error);
}

// Test: Valid 2D (grayscale) cv::Mat should convert to a 2D numpy array.
TEST_F(MatToNumpyTest, Valid2DGrayscale)
{
    const int rows = 5, cols = 4;
    // Create a 2D grayscale cv::Mat (CV_8UC1) with sequential data.
    cv::Mat mat(rows, cols, CV_8UC1);
    for (int i = 0; i < rows; i++)
    {
        for (int j = 0; j < cols; j++)
        {
            mat.at<unsigned char>(i, j) = static_cast<unsigned char>(i * cols + j);
        }
    }

    // Convert cv::Mat to numpy array.
    py::array_t<unsigned char> np_array = mat_to_numpy(mat);
    py::buffer_info buf = np_array.request();

    // Expect a 2D numpy array.
    ASSERT_EQ(buf.ndim, 2);
    EXPECT_EQ(buf.shape[0], static_cast<size_t>(rows));
    EXPECT_EQ(buf.shape[1], static_cast<size_t>(cols));

    // Verify that data is correctly transferred.
    unsigned char *np_data = static_cast<unsigned char *>(buf.ptr);
    for (int i = 0; i < rows; i++)
    {
        for (int j = 0; j < cols; j++)
        {
            EXPECT_EQ(np_data[i * cols + j], mat.at<unsigned char>(i, j));
        }
    }
}

// Test: Valid 3D (color) cv::Mat should convert to a 3D numpy array.
TEST_F(MatToNumpyTest, Valid3DColor)
{
    const int rows = 3, cols = 4, channels = 3;
    // Create a 3D color cv::Mat (CV_8UC3) and fill with a pattern.
    cv::Mat mat(rows, cols, CV_8UC3);
    for (int i = 0; i < rows; i++)
    {
        for (int j = 0; j < cols; j++)
        {
            // For each channel, set pixel value = (i * 10 + j).
            cv::Vec3b pixel;
            for (int c = 0; c < channels; c++)
            {
                pixel[c] = static_cast<unsigned char>(i * 10 + j);
            }
            mat.at<cv::Vec3b>(i, j) = pixel;
        }
    }

    // Convert cv::Mat to numpy array.
    py::array_t<unsigned char> np_array = mat_to_numpy(mat);
    py::buffer_info buf = np_array.request();

    // Expect a 3D numpy array with shape (rows, cols, 3).
    ASSERT_EQ(buf.ndim, 3);
    EXPECT_EQ(buf.shape[0], static_cast<size_t>(rows));
    EXPECT_EQ(buf.shape[1], static_cast<size_t>(cols));
    EXPECT_EQ(buf.shape[2], static_cast<size_t>(channels));

    // Verify pixel values.
    unsigned char *np_data = static_cast<unsigned char *>(buf.ptr);
    size_t pixelSize = channels;
    for (int i = 0; i < rows; i++)
    {
        for (int j = 0; j < cols; j++)
        {
            for (int c = 0; c < channels; c++)
            {
                size_t idx = (i * cols + j) * pixelSize + c;
                EXPECT_EQ(np_data[idx], mat.at<cv::Vec3b>(i, j)[c]);
            }
        }
    }
}

// Test: Empty cv::Mat should cause an exception.
TEST_F(MatToNumpyTest, EmptyMatThrows)
{
    cv::Mat emptyMat;
    EXPECT_THROW({ mat_to_numpy(emptyMat); }, std::runtime_error);
}

// Test: cv::Mat with invalid number of dimensions should throw an error.
TEST_F(MatToNumpyTest, InvalidDimensionsThrows)
{
    // Create a 3D Mat (invalid for images).
    const int dims = 3;
    int sizes[] = {5, 5, 5}; // 5x5x5
    cv::Mat mat(dims, sizes, CV_8UC1);
    EXPECT_THROW({ mat_to_numpy(mat); }, std::runtime_error);
}

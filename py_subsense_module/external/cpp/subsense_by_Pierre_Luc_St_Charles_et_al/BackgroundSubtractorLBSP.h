#pragma once

#include <opencv2/features2d/features2d.hpp>
#include <opencv2/video/background_segm.hpp>
#include "LBSP.h"

/*!
	Local Binary Similarity Pattern (LBSP)-based change detection algorithm (abstract version/base class).

	For more details on the different parameters, see P.-L. St-Charles and G.-A. Bilodeau, "Improving Background
	Subtraction using Local Binary Similarity Patterns", in WACV 2014, or G.-A. Bilodeau et al, "Change Detection
	in Feature Space Using Local Binary Similarity Patterns", in CRV 2013.

	This algorithm is currently NOT thread-safe.
 */
class BackgroundSubtractorLBSP : public cv::BackgroundSubtractor {
public:
	//! full constructor
	BackgroundSubtractorLBSP(float fRelLBSPThreshold, size_t nLBSPThresholdOffset=0);
	//! default destructor
	virtual ~BackgroundSubtractorLBSP();
	//! (re)initiaization method; needs to be called before starting background subtraction
	virtual void initialize(const cv::Mat& oInitImg);
	//! (re)initiaization method; needs to be called before starting background subtraction
	virtual void initialize(const cv::Mat& oInitImg, const cv::Mat& oROI)=0;
	//! primary model update function; the learning param is used to override the internal learning speed (ignored when <= 0)
	virtual void apply(cv::InputArray image, cv::OutputArray fgmask, double learningRate=0)=0;
	//! returns a copy of the ROI used for descriptor extraction
	virtual cv::Mat getROICopy() const;
	//! sets the ROI to be used for descriptor extraction (note: this function will reinit the model and return the usable ROI)
	virtual void setROI(cv::Mat& oROI);
	//! turns automatic model reset on or off
	void setAutomaticModelReset(bool);

protected:
	struct PxInfoBase {
		int nImgCoord_Y;
		int nImgCoord_X;
		size_t nModelIdx;
	};
	//! background model ROI used for LBSP descriptor extraction (specific to the input image size)
	cv::Mat m_oROI;
	//! input image size
	cv::Size m_oImgSize;
	//! input image channel size
	size_t m_nImgChannels;
	//! input image type
	int m_nImgType;
	//! LBSP internal threshold offset value, used to reduce texture noise in dark regions
	const size_t m_nLBSPThresholdOffset;
	//! LBSP relative internal threshold (kept here since we don't keep an LBSP object)
	const float m_fRelLBSPThreshold;
	//! total number of pixels (depends on the input frame size) & total number of relevant pixels
	size_t m_nTotPxCount, m_nTotRelevantPxCount;
	//! current frame index, frame count since last model reset & model reset cooldown counters
	size_t m_nFrameIndex, m_nFramesSinceLastReset, m_nModelResetCooldown;
	//! pre-allocated internal LBSP threshold values LUT for all possible 8-bit intensities
	size_t m_anLBSPThreshold_8bitLUT[UCHAR_MAX+1];
	//! internal pixel index LUT for all relevant analysis regions (based on the provided ROI)
	size_t* m_aPxIdxLUT;
	//! internal pixel info LUT for all possible pixel indexes
	PxInfoBase* m_aPxInfoLUT;
	//! default kernel size for median blur post-proc filtering
	const int m_nDefaultMedianBlurKernelSize;
	//! specifies whether the algorithm is fully initialized or not
	bool m_bInitialized;
	//! specifies whether automatic model resets are enabled or not
	bool m_bAutoModelResetEnabled;
	//! specifies whether the camera is considered moving or not
	bool m_bUsingMovingCamera;
	//! copy of latest pixel intensities (used when refreshing model)
	cv::Mat m_oLastColorFrame;
	//! copy of latest descriptors (used when refreshing model)
	cv::Mat m_oLastDescFrame;
	//! the foreground mask generated by the method at [t-1]
	cv::Mat m_oLastFGMask;

public:
	// ######## DEBUG PURPOSES ONLY ##########
	int nDebugCoordX, nDebugCoordY;
	std::string sDebugName;
};


import cv2 as cv
import cv2.ximgproc
import numpy as np
import os


# This class implements a simple manual segmentation algorithm
# The parameters of the superpixel size are meant to work OK with the touch screen
class Segmentation:

    # This library has been modified by me, in order to work on SPI1 
    def __init__(self, path, imgPath):
        self.path = path
        self.imgPath = imgPath
        self.last = None
        self.original = None
        self.labels = None
        self.lab_mask = None
        self.dim_x = 0
        self.dim_y = 0
        self.selected = None
        self.n_spx =0
        self.done = False

    # Runs the super pixels algorithms.  And inits variables for the sp selection
    def runSuperPixels(self):
        # Open image
        img = cv.imread( self.imgPath , 0) #Open in uint8 only for segmentation

        # MSLIC parameters
        REGION_SIZE = img.shape[1]//20 #70 original value
        RULER = 0.01
        # SLIC parameters 
        NUM_ITERATIONS = 10
        MIN_ELEMENT = 1

        # Use to paint the mask 
        white_img = np.zeros(img.shape, np.uint8)
        white_img[:] = (255)  # White for the mask (only one color)

        # slic = cv.ximgproc.createSuperpixelSLIC(img,algorithm = cv.ximgproc.MSLIC, region_size=REGION_SIZE, ruler=RULER )
        slic = cv.ximgproc.createSuperpixelSLIC(img,region_size=REGION_SIZE, ruler=RULER)
        slic.iterate(NUM_ITERATIONS)

        if (MIN_ELEMENT > 0):
            slic.enforceLabelConnectivity(MIN_ELEMENT)

        self.n_spx = slic.getNumberOfSuperpixels()
        mask = slic.getLabelContourMask(True)

        # stitch foreground margins & background together
        mask_inv = cv.bitwise_not(mask)
        result_bg = cv.bitwise_and(img, img, mask=mask_inv)
        result_fg = cv.bitwise_and(white_img, white_img, mask=mask)
        self.original = cv.add(result_bg, result_fg)

        # get super pixels labels
        self.labels = slic.getLabels()
        # labels = np.array(labels, dtype=np.int32)
        self.lab_mask = np.zeros(self.labels.shape, dtype=np.uint8)

        self.dim_x = img.shape[1]
        self.dim_y = img.shape[0]
        self.selected = [False] * self.n_spx 

        # init mask for the selection 
        self.redImg = np.full( (self.lab_mask.shape[0], self.lab_mask.shape[1], 3), 255, self.lab_mask.dtype)
        self.redImg[:,:] = (0, 0, 255)

        # change result to bgr for showing it on the screen 
        self.original = cv.cvtColor(self.original, cv.COLOR_GRAY2BGR )
        return self.original

    # Updates the selection mask with the new superpixels selected by the user. 
    # px and py are the pixel regions where the user clicked
    def updateSelImage(self, px, py):
        # self.result = cv.circle(self.result, (px,py), radius=5, color=(0,0,255), thickness =3 ) # DEBUG
        sp_index = self.labels[py][px]
        self.selected[sp_index] = not self.selected[sp_index]

        # Apply the selection mask to the pixels
        self.done = False
        for i in range(self.n_spx): 
            if self.selected[i] == True:
                ss = cv.inRange(self.labels, i, i)  
                self.lab_mask = cv.bitwise_or(self.lab_mask, ss)
                self.done = True  # Flag to indicate that at least one superpixel was selected

        # Change the color of the selected super pixels
        redMask = cv2.bitwise_and(self.redImg, self.redImg, mask=self.lab_mask)
        self.last  = cv2.addWeighted(redMask , 0.1, self.original, 0.9, 0)
        return self.last

    # This function save the mask selected with the super pixels
    def saveMask(self):
        mask_path = os.path.join(self.path, 'mask.tiff')

        # convert 8 bit to  16 bit
        img = np.array(self.lab_mask, dtype=np.uint16)
        img *= 256
        cv.imwrite(mask_path, img )  #save image to disk 
                
        

        
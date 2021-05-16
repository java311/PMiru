# # Enables camera to take still photos
    # def enableStillMode(self):
    #     print('Enabling still camera mode')
    #     status = self.camera.get_exposure_status()        
    #     print ("Exposure status: " + str(status))
        
    #     try:
    #         # Force any single exposure to be halted
    #         self.camera.stop_exposure()
    #         self.camera.stop_video_capture()
    #     except (KeyboardInterrupt, SystemExit):
    #         raise
    #     except:
    #         pass

    #     status = self.camera.get_exposure_status()        
    #     print ("Exposure status: " + str(status))

    #     # Set the timeout, units are ms
    #     # TODO why the time out !! ??
    #     timeout = (self.camera.get_control_value(asi.ASI_EXPOSURE)[0] / 1000) * 2 + 50000
    #     print ("timeout value: (ms) " + str(timeout) )
    #     self.camera.default_timeout = timeout
    #     # self.camera.default_timeout = -1
        
    # # Takes single shot, save it on path using the given prefix. 
    # # bit indicates the image forta 8bit (jpeg) or 16bit (tiff) monochrome 
    # def takeSingleShoot(self, path, filename, imgType=8):
    
    #     # if imgType == 8:
    #     #     self.camera.set_image_type(asi.ASI_IMG_RAW8)
    #     # else:
    #     #     self.camera.set_image_type(asi.ASI_IMG_RAW16)
        
    #     self.camera.capture(filename= path + os.path.sep + filename)
        
    #     print('Saved to %s' % filename)
    #     #save_control_values(filename, self.camera.get_control_values())

    # # Enable camera to take video
    # def enableVideoMode(self, imgType):
    #     try:
    #         # Force any single exposure to be halted
    #         self.camera.stop_exposure()
    #     except (KeyboardInterrupt, SystemExit):
    #         raise
    #     except:
    #         pass

    #     if imgType == 8:
    #         self.camera.set_image_type(asi.ASI_IMG_RAW8)
    #         self.imgType = 8
    #     else:
    #         self.camera.set_image_type(asi.ASI_IMG_RAW16)
    #         self.imgType = 16

    #     print('Enabling video mode')
    #     self.camera.start_video_capture()



    # Rotate, change light and take picture
def takeHyperCube():
    camWrap.captureLoop(False) #for zwo camera is necessary to stop the video loop

    #for each slot, rotate to the right 
    if wheel is not None:
        nSlots = wheel.num_slots
    else:
        nSlots = 5

    folder = camWrap.getNewFolder()
    counter = 1
    while (nSlots > 0):
        if wheel is not None:
            wheel.rotateRight()
        time.sleep(1)  #wait for the rotation to finish  #TODO make it a GUI option
        
        leds.nextColorON()  #Next LED color ON
        motor.moveToNextAngle()

        if camType == 'zwo':
            fname = "img_" + format(counter, '02d') + ".tiff"
        else:
            fname = "img_" + format(counter, '02d') + ".tiff"
        camWrap.takeSingleShoot(path=folder, filename=fname)
        nSlots = nSlots -1
        counter = counter + 1

        leds.nextColorOFF()  #Next LED color OFF
    
    # camWrap.rotateImageFiles(folder)  #If ZWO, then rotate the captured images
    camWrap.saveControlValues(path=folder, filename="controlValues.txt")
    camWrap.captureLoop(True)




    # MEDIAN ALGORITM TRASH 

        print (autoMedVals)
    print (autoExpVals)
    print (autoGainVals)

    drops = 5
    avgs = 3
    cycles = 0
    threshold = 5
    g_step = 5.0; e_step = 3
    # gains = [0]*nColors; exps = [0]*nColors; meds = [0]*nColors; ok = [False]*nColors
    gains = autoGainVals; exps = autoExpVals; meds = autoMedVals; ok = [False]*nColors
    ok[darkIndex] = True
    while (cycles <= 10):

        for color in range(0,nColors):
            # if ok[color] == True:
            #     continue

            tmpFilePath = os.getcwd() + os.path.sep + "color_calib_"+ str(color) +"_.tiff"

            # if (meds[color] <= meds[darkIndex]): # increase gain / exp
            #     exps[color] =  exps[color] + e_step
            #     gains[color] =  gains[color] + g_step
            # elif (meds[color] > meds[darkIndex]):  # decrease gain
            #     exps[color] =  exps[color] - e_step
            #     gains[color] =  gains[color] - g_step

            camWrap.set_gain(gains[color])
            camWrap.set_exposure(exps[color])
            leds.colorOnOff(color, True)  # Turn on the darkest LED ON

            meds[color] = camWrap.get_median_singleShoot(tmpFilePath, drops=3, avgs=1)
            # exp = camWrap.get_exposure()   #in microseconds
            # gain = camWrap.get_gain()      #unitless

            # adjust the gain and the median
            # gains[color] = (autoGainVals[darkIndex] * meds[color]) / autoGainVals[darkIndex]
            # exps[color] = (autoExpVals[darkIndex] * meds[color]) / autoExpVals[darkIndex]

            # check if threshold is reached
            print ("color:" +str(color) + " median: " + str(meds[color]) + " difference: "+ str(meds[color] - meds[darkIndex]))
            if abs(meds[color] - meds[darkIndex]) < threshold:
                ok[color] = True

            leds.colorOnOff(color, False)  # Turn on the darkest LED ON
            print (ok)
            print (meds)
            print (exps)
            print (gains)

        #break cycle if all medians are bellow the threshold
        allOk = True
        for color in range(0,leds.nColors):
            if ok[color] == False:
                allOk = False
                break
         
        if allOk == True:
            break

        cycles = cycles +1
        print ('cyclo:' + str(cycles))


    # for color in range(0,leds.nColors): # For each color
    #     if color == darkIndex: #Jump the darkest LED
    #        continue

    #     leds.colorOnOff(color, True)  # Turn on the darkest LED ON

    #     camWrap.set_gain(darkGain)
    #     camWrap.set_exposure(darkExp)
        
    #     median = 0
    #     limit = 1000
    #     while (darkMedian - median > limit):
    #         median = camWrap.get_median(drops=3, avgs=3)
    #         print (darkMedian)
    #         print (median)
    #         print (median - darkMedian)

    #         camWrap.set_gain(darkGain)
    #         camWrap.set_exposure(darkExp)

    #     leds.colorOnOff(color, False)  # Turn on the darkest LED ON
        

    # # sm.get_screen("camera").refreshByFile = False # Disable camera refresh screen


    # # Save the calibration results in config json file



    # If ZWO, then rotate the captured images 
    def rotateImageFiles(self, path, prog_bar, exit_event): 
        if self.camType == 'zwo':
            print ('Rotating image FILES taken with ZWO cameras. This will be slow....')
            ff = []
            prog_bar.value = 0
            for item in self.listdir_fullpath(path):  #openf jpg and tiff
                if os.path.isfile(item) and item.endswith('.jpg'):   
                    ff.append(item)
                if os.path.isfile(item) and item.endswith('.tiff'):  
                    ff.append(item)

            i = 0
            n = len(ff)
            for img_path in ff:
                if exit_event.is_set():
                    print ("Rotation thread killed...")
                    return

                img = Image.open(img_path)
                rimg = ImageOps.flip(img)
                rimg.save(img_path)

                i = i + 1
                prog_bar.value = int((i * 100) / n)
                print ("Rotated: " + img_path + " " + str( int((i * 100) / n) ) + " %")  
        else:
            pass
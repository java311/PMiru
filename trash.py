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
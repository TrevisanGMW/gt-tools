"""
 GT Render Calculator - Script for calculating the time a render will take
 github.com/TrevisanGMW - 2022-07-18

 Work in Progress file

"""
import maya.cmds as cmds
import logging
import datetime

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("gt_utilities")
logger.setLevel(logging.INFO)



def calculate_time(time_per_frame_seconds, num_frames, num_machines):
    # logger.debug('time_per_frame_seconds: ' + str(time_per_frame_seconds))
    # logger.debug('num_frames: ' + str(num_frames))
    # logger.debug('num_machines: ' + str(num_machines))
    date_time = datetime.timedelta(seconds=time_per_frame_seconds)
    # date_time = datetime.now()
    # abc = date_time.strftime("%m/%d/%Y, %H:%M:%S")
    # test = datetime.time(second=date_time.seconds)
    print(date_time)


# seconds
# minutes
# hours
# days

# Build UI
if __name__ == "__main__":
    pass
    time_per_frame_seconds = 610
    num_frames = 5
    num_machines = 2
    logger.setLevel(logging.DEBUG)
    output = calculate_time(time_per_frame_seconds, num_frames, num_machines)
    # build_gui_uv_transfer()

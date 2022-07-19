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
logger = logging.getLogger("gt_render_calculator")
logger.setLevel(logging.INFO)



def calculate_time(time_per_frame_seconds, num_frames, num_machines):
    """

    Args:
        time_per_frame_seconds:
        num_frames:
        num_machines:

    Returns:
        output_time (string): A string describing the duration according to the provided input
    """
    timedelta_sec = datetime.timedelta(seconds=time_per_frame_seconds)
    # timedelta_sec = datetime.timedelta(seconds=time_per_frame_seconds)
    time = datetime.datetime(1, 1, 1) + timedelta_sec

    years = time.year - 1
    months = time.month - 1
    days = time.day - 1
    hours = time.hour
    minutes = time.minute
    seconds = time.second

    logger.debug('########### Detailed Output:')
    logger.debug('years: ' + str(years))
    logger.debug('months: ' + str(months))
    logger.debug('days: ' + str(days))
    logger.debug('hours: ' + str(hours))
    logger.debug('minutes: ' + str(minutes))
    logger.debug('seconds: ' + str(seconds))

    output_time = ''
    if years > 0:
        output_time += str(years) + ' year' + ('' if years == 1 else 's') + '\n'
    if months > 0:
        output_time += str(months) + ' month' + ('' if months == 1 else 's') + '\n'
    if days > 0:
        output_time += str(days) + ' day' + ('' if days == 1 else 's') + '\n'
    if hours > 0:
        output_time += str(hours) + ' hour' + ('' if hours == 1 else 's') + '\n'
    if minutes > 0:
        output_time += str(minutes) + ' minute' + ('' if minutes == 1 else 's') + '\n'
    if seconds > 0:
        output_time += str(seconds) + ' second' + ('' if seconds == 1 else 's') + '\n'

    return output_time


# Build UI
if __name__ == "__main__":
    pass
    time_per_frame_seconds = 60000001
    num_frames = 5
    num_machines = 2
    logger.setLevel(logging.DEBUG)
    output = calculate_time(time_per_frame_seconds, num_frames, num_machines)
    print(output)

import multiprocessing
import logging
import time
#import datetime
import RPi.GPIO as GPIO


class BlinkProcess(multiprocessing.Process):

    def __init__(self):
        multiprocessing.Process.__init__(self)
        self.exitEvent = multiprocessing.Event()
        self.logger = logging.getLogger(__name__)
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(18, GPIO.OUT)

    def run(self):
        self.logger.info("Running blink")

        while not self.exitEvent.is_set():
            sf = time.time() % 1
            if (sf >= 0.0 and sf <= 0.1):
                GPIO.output(18, GPIO.HIGH)
            else:
                GPIO.output(18, GPIO.LOW)
            time.sleep(0.01)

    def terminate(self):
        self.logger.info("Stopping blink")
        GPIO.output(18, GPIO.LOW)
        GPIO.cleanup()
        self.exitEvent.set()

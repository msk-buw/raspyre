import multiprocessing
import logging
import time
#import datetime
#import RPi.GPIO as GPIO


class BlinkProcess(multiprocessing.Process):

    def __init__(self):
        multiprocessing.Process.__init__(self)
        self.exitEvent = multiprocessing.Event()
        self.logger = logging.getLogger(__name__)
        #GPIO.setmode(GPIO.BCM)
        #GPIO.setwarnings(False)
        #GPIO.setup(18, GPIO.OUT)

    def run(self):
        self.logger.info("Running blink")

        with open("/sys/class/leds/led1/trigger", "w") as power_led:
            with open("/sys/class/leds/led0/trigger", "w") as act_led:
                while not self.exitEvent.is_set():
                    sf = time.time() % 1
                    if (sf >= 0.0 and sf <= 0.1):
                        #GPIO.output(18, GPIO.HIGH)
                        power_led.seek(0)
                        act_led.seek(0)
                        power_led.write('default-on\0')
                        act_led.write('default-on\0')
                    else:
                        #GPIO.output(18, GPIO.LOW)
                        power_led.seek(0)
                        act_led.seek(0)
                        power_led.write('none\0')
                        act_led.write('none\0')
                    time.sleep(0.01)
        with open("/sys/class/leds/led1/trigger", "w") as power_led:
            power_led.seek(0)
            power_led.write('default-on\0')
        with open("/sys/class/leds/led0/trigger", "w") as act_led:
            act_led.seek(0)
            act_led.write('mmc0\0')

    def terminate(self):
        self.logger.info("Stopping blink")
        #GPIO.output(18, GPIO.LOW)
        #GPIO.cleanup()
        # set default states
        
        self.exitEvent.set()


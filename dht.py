import time
import Adafruit_DHT as dht

#sensor = Adafruit_DHT.DHT22

#pin = 7

#try:

while True:

        h,t = dht.read_retry(dht.DHT22,4)

        if h is not None and t is not None :
            print("Temperature = {0:0.1f}*C Humidity = {1:0.1f}%".format(t, h))
            time.sleep(1)
        else :
            print('Read error')
            time.sleep(100)
#except KeyboardInterrupt:
#    print("Terminated by Keyboard")

#finally:
#    print("End of Program")

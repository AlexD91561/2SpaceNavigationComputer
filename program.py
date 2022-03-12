from bmp180 import BMP180
import sdcard
import uos
from machine import Pin, I2C
from time import sleep_ms
import time
import _thread
import machine
#define connection with IMU
adr = 0x68 # i2c address for the MPU6050
pscl = Pin(21) # SCL pin
psda = Pin(20) # SDA pin
i2c_IMU = I2C(0, scl=pscl, sda=psda, freq=100*1000) # initialize i2c object


# define pressure sensor

i2c_BMP =  I2C(0,scl=Pin(21), sda=Pin(20), freq=100000)
bmp180 = BMP180(i2c_BMP)

bmp180.oversample_sett = 2
bmp180.baseline = 101325

#define SDCard
# Assign chip select (CS) pin (and start it high)
# cs = machine.Pin(9, machine.Pin.OUT)

# Intialize SPI peripheral (start with 1 MHz)
# spi = machine.SPI(1,
#                   baudrate=1000000,
#                   polarity=0,
#                   phase=0,
#                   bits=8,
#                   firstbit=machine.SPI.MSB,
#                   sck=machine.Pin(10),
#                   mosi=machine.Pin(11),
#                   miso=machine.Pin(8))
# 
# sd = sdcard.SDCard(spi, cs)
# 
# # Mount filesystem
# vfs = uos.VfsFat(sd)
# uos.mount(vfs, "/SD")

# Create a file and write something to it
# with open("/SD/file_counter.txt", "w") as file:
#    file.write("0")

# Open the file we just created and read from it
# try:
#     with open("/SD/file_counter.txt", "r") as file:
#         
#         file_counter = file.read()
#         file_counter = int(file_counter)
# except:
#     with open("/SD/file_counter.txt", "w") as file:
#         file.write("0")
#     file_counter=0
# # resets the MPU-6050
# # must be called before using it

# def increase_file_counter(counter):
#     counter+=1
#     with open("/SD/file_counter.txt", "w") as file:
#         file.write(str(counter))
# 
def reset():
#      write to PWR_MGMT_1 the value 0
     # this resets the MPU-6050
     
     i2c_IMU.writeto(adr, b'\x6B\x00', True)
     # wait for it to reset
     # idk if this is necessary. I just put it here
     sleep_ms(50)
    
# #reads accelerometer, gyro, and temp data and outputs them over serial
def read_data():
        # write ACCEL_XOUT_H without Stop
    i2c_IMU.writeto(adr, b'\x3B', False)
    # and read 14 bytes
    r = i2c_IMU.readfrom(adr, 14, True)

    # split byte array into ints
    ax = (r[0] << 8) | r[1]
    ay = (r[2] << 8) | r[3]
    az = (r[4] << 8) | r[5]
    t  = (r[6] << 8) | r[7]
    gx = (r[8] << 8) | r[9]
    gy = (r[10] << 8) | r[11]
    gz = (r[12] << 8) | r[13]
        
#     # Magic. Skip over this part if you care about your sanity.
#     # Or please read it and improove it if you are some sort of python wizard.
#     # I can not put into words how frustrating figuring this out was.
#     # It took too fucking long. And I knew what was wrong from the start
#     # because I wrote this first in C. Alas, python and its lack of types
#     # make it really really difficult to take two bytes and convert it to
#     # a 16 bit signed integer. Especially when python doesn't have a fixed
#     # length for ints.
    
    # So what we are trying to do here is sign extend to an unknown number
    # of bits.
    
    # The function int.from_bytes(bytes, byteorder, *, signed=False)
    # seems like the perfect candidate for this. Sadly it doesn't work.
    # It works on my computer, but not on the Raspberry Pi.
    # This is likely microPython's fault. I did not research further.
    
    # We are left with no other choice but to use the dark magic of
    # programming: evil bit hacks. I will do my best to explain how
    # this works. Since this has to be done for each variable I will
    # use the letter v in it's place.
    
    # Currently the least signigicant bits of v contain the two bytes
    # that we read from the MPU-6050. The rest are leading zeros (only
    # god knows how many). So to check if we need sign extending at all
    # we just use a mask for bit 15. If this bit is set, we need to extend.
    # This is done by taking -1, which has the binary representation of all
    # ones (we don't know how many), xor-ing it with 0xFFFF which flips
    # the first 16 bits ( and-ing would have probably worked too), and
    # or-ing the result with v (set the last 16 bits to v)
    
    # This method is dirty. I'm not proud of it. There should be a more
    # elegant sollution that probably just didn't come to mind. If you
    # read this far and belive you might be able to come up with that
    # sollution I invite you to try and if you succeed to purge the record
    # of my pain from this code.
    
    # p.s. in C, a simple cast in the line above saves us from all the hell
    # bellow. I am leaving that line of code here for you to gaze at its
    # simplicity: v = ((int)r[0] << 8) | r[1];
#     
    if (ax & (1<<15)) != 0:
        ax = (-1 ^ 0xFFFF) | ax
    if (ay & (1<<15)) != 0:
        ay = (-1 ^ 0xFFFF) | ay
    if (az & (1<<15)) != 0:
        az = (-1 ^ 0xFFFF) | az
    if (gx & (1<<15)) != 0:
        gx = (-1 ^ 0xFFFF) | gx
    if (gy & (1<<15)) != 0:
        gy = (-1 ^ 0xFFFF) | gy
    if (gz & (1<<15)) != 0:
        gz = (-1 ^ 0xFFFF) | gz
    if (t & (1<<15)) != 0:
        t = (-1 ^ 0xFFFF) | t
    
    # print out results in Arduino Serial Plotter format
    #print('ax:',ax,' ay:',ay,' az:',az, sep='',end=' ')
    #print('gx:',gx,' gy:',gy,' gz:',gz, sep='',end='')
    #print(' t:',t, sep='')
    return ax,ay,az,gx,gy,gz

def altitude_IBF(pressure):
    alt = 44331.5 - 4946.62 * pressure ** (0.190263)
    return alt

# # main program




# increase_file_counter(file_counter)
# print(f'file_counter = {file_counter}')
# 
# name_file = "/SD/flight_data_" + str(file_counter) + ".txt"
# name_file_csv = "/SD/flight_data_" + str(file_counter) + ".csv"
timestamp=0
# 
# #write the fields in csv
# field_names = "pressure altitude temperature ax ay az gx gy gz timestamp\n"
# with open(name_file_csv, "a") as file:
#         file.write(field_names)
#

reset()
while True:
    start_time = time.ticks_ms()
    ax,ay,az,gx,gy,gz = read_data()
    pressure = bmp180.pressure #Pa
    altitude = altitude_IBF(pressure)
    #todo temperatura
    result_str = str(pressure) + " " + str(altitude) + " " + str(0) + " " + str(ax) +" "+ str(ay) +" "+ str(az) +" "+ str(gx) +" "+ str(gy) +" "+ str(gz) +" "+ str(timestamp) + '\n'
    
    
#     #write the results in file_data text file
#     with open(name_file_csv, "a") as file:
#         file.write(result_str)
#     print(pressure, altitude, ax, ay, az , timestamp)
    
   
    
    #print(f'ax={ax} ,\nay={ay} ,\naz = {az} ,\ngx={gx} ,\ngy={gy} ,\ngz={gz},\npressure(hPa)={pressure} ,\naltitude_from_pressure={altitude}\n')
    timestamp = timestamp + (time.ticks_ms() - start_time)
    #sleep_ms(timestamp)



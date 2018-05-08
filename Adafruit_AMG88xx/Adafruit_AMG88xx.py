# Copyright (c) 2017 Adafruit Industries
# Author: Dean Miller
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import logging
from Adafruit_bitfield import Adafruit_bitfield

# AMG88xx default address.
AMG88xx_I2CADDR	= 0x69

AMG88xx_PCTL 	= 0x00
AMG88xx_RST 	= 0x01
AMG88xx_FPSC 	= 0x02
AMG88xx_INTC 	= 0x03
AMG88xx_STAT 	= 0x04
AMG88xx_SCLR 	= 0x05
#0x06 reserved
AMG88xx_AVE 	= 0x07
AMG88xx_INTHL 	= 0x08
AMG88xx_INTHH 	= 0x09
AMG88xx_INTLL 	= 0x0A
AMG88xx_INTLH 	= 0x0B
AMG88xx_IHYSL 	= 0x0C
AMG88xx_IHYSH 	= 0x0D
AMG88xx_TTHL 	= 0x0E
AMG88xx_TTHH 	= 0x0F
AMG88xx_INT_OFFSET = 0x010
AMG88xx_PIXEL_OFFSET = 0x80

# Operating Modes
AMG88xx_NORMAL_MODE = 0x00
AMG88xx_SLEEP_MODE = 0x01
AMG88xx_STAND_BY_60 = 0x20
AMG88xx_STAND_BY_10 = 0x21

#sw resets
AMG88xx_FLAG_RESET = 0x30
AMG88xx_INITIAL_RESET = 0x3F
	
#frame rates
AMG88xx_FPS_10 = 0x00
AMG88xx_FPS_1 = 0x01
	
#int enables
AMG88xx_INT_DISABLED = 0x00
AMG88xx_INT_ENABLED = 0x01
	
#int modes
AMG88xx_DIFFERENCE = 0x00
AMG88xx_ABSOLUTE_VALUE = 0x01

AMG88xx_PIXEL_ARRAY_SIZE = 64
AMG88xx_PIXEL_TEMP_CONVERSION = .25
AMG88xx_THERMISTOR_CONVERSION = .0625

def constrain(val, min_val, max_val):
    return min(max_val, max(min_val, val))
		

class Adafruit_AMG88xx(object):
	def __init__(self, mode=AMG88xx_NORMAL_MODE, address=AMG88xx_I2CADDR, i2c=None, **kwargs):
		self._logger = logging.getLogger('Adafruit_BMP.BMP085')
		# Check that mode is valid.
		if mode not in [AMG88xx_NORMAL_MODE, AMG88xx_SLEEP_MODE, AMG88xx_STAND_BY_60, AMG88xx_STAND_BY_10]:
			raise ValueError('Unexpected mode value {0}.  Set mode to one of AMG88xx_NORMAL_MODE, AMG88xx_SLEEP_MODE, AMG88xx_STAND_BY_60, or AMG88xx_STAND_BY_10'.format(mode))
		self._mode = mode
		# Create I2C device.
		if i2c is None:
			import Adafruit_GPIO.I2C as I2C
			i2c = I2C
		self._device = i2c.get_i2c_device(address, **kwargs)

		#set up the registers
		self._pctl = Adafruit_bitfield([('PCTL', 8)])
		self._rst = Adafruit_bitfield([('RST', 8)])
		self._fpsc = Adafruit_bitfield([('FPS', 1)])
		self._intc = Adafruit_bitfield([('INTEN', 1), ('INTMOD', 1)])
		self._stat = Adafruit_bitfield([('unused', 1), ('INTF', 1), ('OVF_IRS', 1), ('OVF_THS', 1)])
		self._sclr = Adafruit_bitfield([('unused', 1), ('INTCLR', 1), ('OVS_CLR', 1), ('OVT_CLR', 1)])
		self._ave = Adafruit_bitfield([('unused', 5), ('MAMOD', 1)])

		self._inthl = Adafruit_bitfield([('INT_LVL_H', 8)])
		self._inthh = Adafruit_bitfield([('INT_LVL_H', 4)])

		self._intll = Adafruit_bitfield([('INT_LVL_H', 8)])
		self._intlh = Adafruit_bitfield([('INT_LVL_L', 4)])

		self._ihysl = Adafruit_bitfield([('INT_HYS', 8)])
		self._ihysh = Adafruit_bitfield([('INT_HYS', 4)])

		self._tthl = Adafruit_bitfield([('TEMP', 8)])
		self._tthh = Adafruit_bitfield([('TEMP',3), ('SIGN',1)])

		#enter normal mode
		self._pctl.PCTL = self._mode
		self._device.write8(AMG88xx_PCTL, self._pctl.get())

		#software reset
		self._rst.RST = AMG88xx_INITIAL_RESET
		self._device.write8(AMG88xx_RST, self._rst.get())

		#disable interrupts by default
		self.disableInterrupt()

		#set to 10 FPS
		self._fpsc.FPS = AMG88xx_FPS_10
		self._device.write8(AMG88xx_FPSC, self._fpsc.get())

	def setMovingAverageMode(self, mode):
		self._ave.MAMOD = mode
		self._device.write8(AMG88xx_AVE, self._ave.get())

	def setInterruptLevels(self, high, low, hysteresis):

		highConv = int(high / AMG88xx_PIXEL_TEMP_CONVERSION)
		highConv = constrain(highConv, -4095, 4095)
		self._inthl.INT_LVL_H = highConv & 0xFF

		self._inthh.INT_LVL_H = (highConv & 0xF) >> 4
		self._device.write8(AMG88xx_INTHL, self._inthl.get())
		self._device.write8(AMG88xx_INTHH, self._inthh.get())

		lowConv = int(low / AMG88xx_PIXEL_TEMP_CONVERSION)
		lowConv = constrain(lowConv, -4095, 4095)
		self._intll.INT_LVL_L = lowConv & 0xFF
		self._intlh.INT_LVL_L = (lowConv & 0xF) >> 4
		self._device.write8(AMG88xx_INTLL, self._intll.get())
		self._device.write8(AMG88xx_INTLH, self._intlh.get())

		hysConv = int(hysteresis / AMG88xx_PIXEL_TEMP_CONVERSION)
		hysConv = constrain(hysConv, -4095, 4095)
		self._ihysl.INT_HYS = hysConv & 0xFF
		self._ihysh.INT_HYS = (hysConv & 0xF) >> 4
		self._device.write8(AMG88xx_IHYSL, self._ihysl.get())
		self._device.write8(AMG88xx_IHYSH, self._ihysh.get())


	def enableInterrupt(self):

		self._intc.INTEN = 1
		self._device.write8(AMG88xx_INTC, self._intc.get())


	def disableInterrupt(self):

		self._intc.INTEN = 0
		self._device.write8(AMG88xx_INTC, self._intc.get())


	def setInterruptMode(self, mode):

		self._intc.INTMOD = mode
		self._device.write8(AMG88xx_INTC, self._intc.get())


	def getInterrupt(self):
		buf = []
		for i in range(0, 8):
			buf.append(self._device.readU8(AMG88xx_INT_OFFSET + i))
			
		return buf

	def clearInterrupt(self):

		_rst.RST = AMG88xx_FLAG_RESET
		sefl._device.write8(AMG88xx_RST, self._rst.get())


	def readThermistor(self):

		raw = self._device.readU16(AMG88xx_TTHL)
		return self.signedMag12ToFloat(raw) * AMG88xx_THERMISTOR_CONVERSION
	
	def readPixels(self):
		buf = []
	
		for i in range(0, AMG88xx_PIXEL_ARRAY_SIZE):
			raw = self._device.readU16(AMG88xx_PIXEL_OFFSET + (i << 1))
			
			converted = self.twoCompl12(raw) * AMG88xx_PIXEL_TEMP_CONVERSION
			buf.append(converted)
			
		return buf

	def twoCompl12(self, val):
		if  0x7FF & val == val:
			return float(val)
		else:
			return float(val-4096 )

	def signedMag12ToFloat(self, val):
		#take first 11 bits as absolute val
		if  0x7FF & val == val:
			return float(val)
		else:
			return  - float(0x7FF & val)

		
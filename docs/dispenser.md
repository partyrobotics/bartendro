Documentation for Bartendro Dispenser

Functional overview
===================

The Bartendro Dispenser can dispense liquid with milliliter accuracy and can be 
used in a stand alone system or in combination with a router and other pumps to create a more
complex liquid dispensing system.

The functions this dispenser can perform are:

- Run the pump for a number of milliseconds.
- Run the pump for a number of rotations (or quarters of rotations)
- Set the built-in LED colors and run LED animations
- Estimate the amount of liquid left in a bottle
- Sense when the pump is seizing and shut off power to the motor
- Track use of the pump using number of rotations.


Hardware overview
=================

Bartendro uses a star network topology using RS-232 (serial) communications.
A Bartendro drink bot usually contains a Raspberry Pi (RPI), a router board for communicating 
with dispensers and up to 15 dispensers. Using the router, the RPI can select one dispenser at
a time and communicate with it or communicate in broadcast mode to all of the dispensers at the 
same time. 

While these docs focus on discussing the dispensers, you need to be aware of what the router
does in order to fully understand all of the communication nuances of our dispensers. Because
of the router, each dispenser is programmed with a dispenser id that uniquely identifies a 
dispenser in the system. This id needs to be received from the dispenser at the start of the 
communication with the dispenser.

Each dispenser also contains 4 tri-color LEDs connected to a WS2801 LED driver chip that handles
the PWM functions to set the LEDs to a given color. All LEDs in one dispenser are connected
to one WS2801 chip and cannot be independently addressed. Given that the RPI cannot communicate
with all of the dispensers at exactly the same time, we've included a SYNC signal from the router
to each of the dispensers. This SYNC signal is used to synchronize LED animation patterns
stored in the dispensers. The dispenser changes the color of the LEDs based on the stored
pattern periodically based on the SYNC signal.

Communicating with a dispenser
==============================

After power up, the LEDs in the pumps will turn blue, waiting for communication. If a pump 
starts up and has a solid red color, its is missing a dispenser id that needs to be 
programmed into eeprom. See eeprom section for more information on this.

To initiate communication, the user should send the question mark character '?' to the pump. 
The dispenser will respond with a one byte response that is its dispenser id. The dispenser 
will continue to respond to '?' characters until it receives a 0xFF character, indicating that 
the dispenser user has captured the dispenser id and communication can start. The user should 
save the dispenser id as it will be required to address the dispense in subsequent communication.

Once the dispenser is ready for communication it will display its "idle" LED pattern which is a 
rainbow color changing pattern. At this point the dispenser is ready to receive a packet
of data. Now the user may send a packet of data to the dispenser. The dispenser will respond
with either a single byte ACK code, or a complete packet, depending on the type of
packet that was sent.

Each packet contains a destination field, which is the dispenser id that was captured
in the beginning of communication with the dispenser. While this may seem silly in a single
dispenser setup, its important when more than one dispenser is used in conjunction with 
a router. All packets sent from the router are sent over one serial TX line to ALL dispensers
connected to the router. All dispensers receive the packets and if the packet is not
marked as a broadcast packet or marked with its dispenser id, the dispenser will ignore
the packet. If a dispenser receives a packet that is a broadcast packet it must take the
appropriate action and NOT SEND a response. Broadcast packets should NEVER be replied to. 
If a dispenser receives a packet with its dispenser id, it must take action and then 
send a response to the user. Depending on the packet type, a response can either be 
a single character ACK code, or a complete packet in response.

For more information on how packets are structured, packet types and if they require
a response, see the detailed packet sections below.

Packet structure
================

Packets are comprised of two sections:

 * Header: 2 characters, always 0xFF 0xFF
 * Packet body, which is 7 bit data escaped, 10 bytes long

This packet body must be encoded into 7 bit data, so that the MSB of any data in the packet will
never be set. This allows the dispenser to clearly identify a packet header, which is the 
only data to ever have the MSB set in an entire packet. For details on how to encode data
to 7 bits, please see firmware/common/pack7.c[|h]. 

The data in the packet, when unpacked is 8 bytes long:

 * unsigned byte: destination dispenser id -- the dispenser id discovered during the 
   communication setup or BROADCAST_DEST.
 * unsigned byte: packet type -- one of the packet types described below
 * 4 bytes of payload data -- Either a 32 bit value, 2 16 bit values or 4 8 bit values.
 * unsigned 16 bit word: 16 bit CRC value calculated for the destination, type and payload
   value. For the details of this algorithm, see the function crc16_update() in
   ui/bartendro/router/driver.py


Sending packets
===============

Packets should be sent to the dispensers with a baud rate of 9600, no party and 1 stop bit.
After sending 10 bytes, the user should wait until the dispenser sends a response. Most packet 
types will get a single byte ACK code response and some will get a complete packet as a response.
Packets that receive a full response are:

 * PACKET_IS_DISPENSING 
 * PACKET_LIQUID_LEVEL
 * PACKET_UPDATE_LIQUID_LEVEL
 * PACKET_SAVED_TICK_COUNT
 * PACKET_GET_LIQUID_THRESHOLDS

All other packet types will receive a simple ACK code, consisting of one of the following:

 * 0 - PACKET_ACK_OK       -- packet received OK and acted upon
 * 1 - PACKET_ACK_CRC_FAIL -- packet data was corrupt and was not executed
 * 3 - PACKET_ACK_INVALID  -- the packed was improperly packed to 7 bits and did not yield 8
                              bytes of packet data.
 * 4 - PACKET_ACK_INVALID_HEADER -- an incomplete header (only one 0xFF character) was received
 * 5 - PACKET_ACK_HEADER_IN_PACKET -- An header character (0xFF) was received in a packet, 
                                      which is invalid.

For any packet that requires a complete response (any packet that returns data and not just an 
ACK) the dispenser will respond by sending a complete packet in response. Once this packet has
been received by the user, a single character ACK, as described above, must be sent to the
dispenser.

Packet types
============

The following packets can be set to/from the dispenser:

* PACKET_PING -- A diagnostic to see if the dispenser is alive. No action is taken. Contains
  no data payload.
* PACKET_SET_MOTOR_SPEED -- Turn the motor on at a given speed. The max speed is 255, which 
  should be suitable for most applications. If you'd like the dispenser to turn more slowly, 
  you can give it a slower speed. Slower speeds can be useful for dispensing smaller quantities
  of liquid or where more fine grained control is required. We recommend to not set the speed
  below 64, since at that speed the motor can barely overcome the friction to turn the pump.
  To turn the pump off completely, set the speed to 0. Once this command is initiated, the 
  dispenser will immediately return an ACK and it will not wait for the dispense function to 
  complete. Data payload is motor speed as a 8 bit unsigned int in the first byte and wether
  or not to enable over current sense in the second 8 bit unsigned int.
* PACKET_TICK_SPEED_DISPENSE -- Dispense for a certain number of ticks at a given speed. Dispenser
  rotation is measured in "ticks" which are generated by magnets moving over hall sensors in the 
  dispenser. There are 4 hall sensors, so it takes 4 ticks for the pump to make one full turn. 
  This function is the most accurate way to dispense a liquid. We've determined that the pump 
  dispenses 1 milliliter in 2.78 ticks. Once this command is initiated, the dispenser will 
  immediately return an ACK and it will not wait for the dispense function to complete. The number
  of ticks to dispense is an unsigned 16 bit payload and the speed to dispense (max speed is
  255!) is the second unsigned 16 bit payload.
* PACKET_TIME_DISPENSE -- Dispense for a certain number of milliseconds. The 32 bit payload
  determines the number of milliseconds the pump should run for. Tick counting is completely
  ignored with this command. Payload is a 32 bit unsigned integer.
* PACKET_LED_OFF -- Turn off the LEDs in the dispenser. No payload.
* PACKET_LED_IDLE -- Display the "idle" pattern in the dispenser. No payload.
* PACKET_LED_DISPENSE -- Display the "dispense" pattern on the LEDs. No payload.
* PACKET_LED_DRINK_DONE -- Display the "drink done" pattern. No payload.
* PACKET_IS_DISPENSING -- This function asks the dispenser if it is still dispensing. Since
  the dispense commands return immediately and don't wait for the dispense to complete,
  the user needs a method to determine if a dispense is complete. This call enables that.
  This packet requires a complete packet response. There is no data payload for the
  request sent from the user, but the dispenser responds with a boolean response (is dispensing)
  in the first byte of the payload and if the over current sensor has been triggered in the 
  second byte of the payload.
* PACKET_LIQUID_LEVEL -- If a dispenser is equipped with a liquid level sensor, this call
  will return the liquid level saved in the dispenser's ram. Liquid levels are not read on 
  the fly -- instead a stored value will be returned to the user. To update the stored value 
  with the current value use the PACKET_UPDATE_LIQUID_LEVEL command. The liquid level in the 
  bottle (or whatever vessel might be used) is expressed as 10 bit value (0 - 1024). Liquid
  level sensors are sensitive devices that require a minor amount of calibration. Each liquid
  level sensor may have a slightly different idea of what "empty" means. For more information
  on how to interpret these values, please see the section "liquid level sensors". If the
  dispenser is not equipped with a liquid level sensor, the values returned by this command
  are undefined. This packet requires a full packet response. Packets sent to the dispenser
  contain no payload. Packets sent from the dispenser contain a 10 bit value in the
  first 16 bit value in the payload.
* PACKET_UPDATE_LIQUID_LEVEL -- Use this command to force the dispenser to update the 
  current liquid level. We recommend that you let at least 5ms pass between updating the 
  liquid levels with this command and reading them with PACKET_LIQUID_LEVEL. No payload.
* PACKET_ID_CONFLICT -- If two dispensers connected to one router have the same dispenser id,
  it creates an ID conflict. This command turns the pump LEDs red and cause the pump to
  do nothing until it is reset. No payload.
* PACKET_LED_CLEAN -- Set the LEDs to the "clean" pattern. No payload.
* PACKET_SET_CS_THRESHOLD -- This command sets the threshold value at which the motor is 
  considered to be seized and should be turned off. This can happen when hoses get old or
  are otherwise obstructed. To prevent the motor from burning out, the current sensor
  determines when a motor is working too hard and shuts off the pump. The default value
  programmed into the dispensers should suffice for most uses. For more information see
  the section "over current protection". The current sense limit should be given in 
  the first 16 bit value of the payload.
* PACKET_SAVED_TICK_COUNT -- This command retrieves the tick count saved in the dispenser's
  eeprom memory. It tells you how many ticks (turns if you divide ticks by 4) the dispenser
  has turned since the tick counter was reset. This feature is to measure hose life and to give
  the user of the dispenser an idea when the hoses inside the pump need to be replaced. This
  packet requires a full packet response. Packets sent to the dispenser contain no payload. 
  Packets sent from the dispenser contain a 10 bit value in the first 16 bit value in the payload.
* PACKET_RESET_SAVED_TICK_COUNT -- This command resets the stored tick count in the dispenser's
  eeprom memory. This value should only be reset when the hoses inside the dispenser have been
  changed. No payload.
* PACKET_GET_LIQUID_THRESHOLDS -- This command is used to query the liquid out thresholds stored
  in the dispenser's eeprom memory. This packet requires a full response and the response packet
  will contain two 16 bit values: "low" threshold and "out" threshold. For more information
  on liquid level thresholds, please see the section "liquid level sensors". The first
  16 bit value of the payload is the "low" threshold and the second 16 bit value is the "out"
  threshold.
* PACKET_SET_LIQUID_THRESHOLDS -- This command sets the liquid level thresholds. Two 16 bit 
  values for "low" threshold and "out" should be contained in the packet. For more information
  on liquid level thresholds, please see the section "liquid level sensors".
* PACKET_FLUSH_SAVED_TICK_COUNT -- This command should be sent to the dispenser before shutting 
  down the dispenser. The dispenser keeps track of the current tick count in RAM and only 
  flushes it to eeprom periodically to prevent the eeprom memory from wearing out. To ensure 
  that the accurate tick counts are stored in the pump, make sure to call this command before 
  shutting down the dispenser. No payload.

Deprecated commands:

* PACKET_TICK_DISPENSE -- Dispense for a certain number of ticks. Pump rotation is measured in
  "ticks" which are generated by magnets moving over hall sensors in the dispenser. There
  are 4 hall sensors, so it takes 4 ticks for the pump to make one full turn. This function
  is the most accurate way to dispense a liquid. We've determined that the pump dispenses
  1 milliliter in 2.78 ticks. Once this command is initiated, the dispenser will immediately
  return an ACK and it will not wait for the dispense function to complete. The number
  of ticks to dispense is an unsigned 32 bit payload, but only the 16 bits of data will be used.
  This command is deprecated in favor of the PACKET_TICK_SPEED_DISPENSE that allows the user
  to specify the speed with which to dispense.

EEPROM
======

The EEPROM of the Atmel atmega168a micro-controller contains the following pieces of
data:

   offset     data type         data
   0          8 bit unsigned    Dispenser id
   1          32 bit unsigned   Run count in ticks
   5          16 bit unsigned   Liquid "low" threshold
   7          16 bit unsigned   Liquid "out" threshold

To get a working dispenser, you will need at least to minimally write a dispenser id 
into the first byte into eeprom RAM. This can be any value but 0 or 255. 

Dispensers shipped from PartyRobotics have this dispenser id set. You can set another
dispenser id (chosen randomly) by running the script in /firmware/dispenser/pump.sh

Resetting the dispenser
=======================

To reset the dispenser, the user needs to hold the RESET line high for at least 1ms. This will
do a software reset that causes the dispenser to stop what it is currently doing and
enter the address discovery mode as it normally would on startup.

Liquid level sensors
====================

The liquid level sensors that are available for our dispensers allow the dispenser to
estimate the amount of liquid left in a bottle. The "liquid level" sensors are really
differential pressure sensors that measure the difference between ambient air pressure
and a liquid level hose that rests in the bottle. The liquid in the bottle exerts a tiny
amount of pressure on the hose and there for on the sensor. As the liquid level in the
bottle drops, the pressure approaches the ambient pressure. Once the pressure exerted
on the hose is equal to ambient pressure, the bottle is empty. 

Care should be given to never empty a bottle fully, because if the intake hose sucks
air while dispensing, an inaccurate dispense occurs. To avoid this, the liquid "out"
threshold should be set conservatively so that the dispenser will consider a bottle to
be empty before it is actually empty.

These sensors are sensitive devices that require some calibration. Even at ambient 
air pressure, not all sensors are going to return the value absolute value. Depending on
how you plan to use the pressure sensors we encourage you to read the pressure sensor
readings at different liquid levels to get acquainted with how the sensor works.

Over current protection
=======================

Each dispenser also comes equipped with an "over current sense" circuit. This
circuit estimates the amount of current that the motor in the dispenser consumes. If for
some reason the motor binds up and consumes large amounts of current, the dispenser
stops the motor and flashes the red LEDs quickly. At this point the dispenser refuses
to engage the motor again until the dispense has been reset. 

Empirical testing has shown that the default value of 465 works well for the motor
running at full speed. You can provide different current sense threshold values
using the PACKET_SET_CS_THRESHOLD command.

Color error codes
=================

The dispenser's only real form of end-user feedback is the color of the dispenser. The
following colors/animations are programmed into the stock dispenser:

* Solid RED at startup: id conflict
* Solid BLUE at startup: ready for communication, waiting for user to initiate 
  communication.
* Solid GREEN: A 0xFF character has been received after communication startup. The
  dispenser is now waiting for the first command from the user.
* Rainbow color animation: idle mode. The dispenser is waiting for commands from the user.
* Red <-> blue color animation: Dispenser is dispensing liquids.
* Pulsing green color animation: Dispsener is done dispensing liquids.
* Pulsing purple color animation: Dispenser is currently being cleaned. This mode really
  only has significance in the context of a larger setup where the RPI can execute
  a clean cycle using multiple dispensers.

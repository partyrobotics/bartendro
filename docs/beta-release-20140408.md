Upgrade instructions for Bartendro software beta 2014-04-08
===========================================================

This software release is BETA quality, meaning that you may encounter bugs in the software.
Please do not use this for important parties. :)

If you find problems with the new software, please report them here:

https://github.com/partyrobotics/bartendro/issues/new

**REALLY IMPORTANT NOTES -- Please read the following before proceeding!**

* PLEASE READ THE WHOLE INSTRUCTIONS BEFORE YOU BEGIN!
* We recommend using a separate empty 4GB SD Card for this beta release. **WE DO NOT
RECOMMEND THAT YOU OVERWRITE YOUR CURRENT BARTENDRO SD CARD!!**


Download the beta release
-------------------------

To start, download this file:

ftp://download.partyrobotics.com/pub/partyrobotics/bartendro/images/beta-release-20140408.zip

Alternatively, if you know how to use 7zip, you can download this much smaller file:

ftp://download.partyrobotics.com/pub/partyrobotics/bartendro/images/beta-release-20140408.7z

While one of the above files downloads, fire up your Bartendro and go to the options tab
in the admin interface for Bartendro ( /admin/options ). You should do this using a laptop or a PC
so that you can download Bartendro's database and save it to your machine. On the options
screen, look for the Database box and then click on the "Download Database" button. This will cause
the Bartendro database file to be downloaded to your local computer. Save this file in a location
where you can find it later. Ideally, drop it into something like DropBox for safe keeping.

When the download of the software update finishes, extract the .img file by double clicking on
the .zip file. Most modern OSes will extract the .img file and place it into the same directory
where you downloaded the zip file. For the new step, you'll need a separate 4GB SD card like
this one:

http://www.amazon.com/SanDisk-Ultra-Class-Memory-SDSDU-032G-AFFP

We recommend SanDisk (they fail less often) and the speed class 10 -- this will make your Bartendro
run nice and fast. You may also use a larger capacity SD card, but it won't make a real difference 
how Bartendro runs.

Write the image to the new SD Card
----------------------------------

Next, write the image you downloaded onto the SD Card. These instructions cover all the bases for
getting this job done. Please note that you can skip the part about "Downloading an Image", "Choose
your Operating System" and "Choose your distribution". You're going to write the .img file you've 
already downloaded. Other than that, follow these instructions exactly:

http://learn.adafruit.com/downloads/pdf/adafruit-raspberry-pi-lesson-1-preparing-and-sd-card-for-your-raspberry-pi.pdf

Install the new SD Card into Bartendro
--------------------------------------

Once you've managed to write the SD Card, you're ready to swap out the current SD Card for the one
in your Bartendro. IMPORTANT: Turn off your Bartendro. If you fail to turn off your Bartendro before
swapping out the cards, you're going to damage the Raspberry Pi that runs everything. 

**AGAIN: Turn off Bartendro. In fact, unplug it from wall-power!**

If you have a Bartendro 7 or Bartendro 15, it might be easier to perform the next step with Bartendro
set upside down on its head. This next step is somewhat fiddely, due to the limited space inside the
bot.  TIP: Grab a camera(phone) and take a picture of the underside of your Bartendro to see where
each of the black cables connect to. This way you can reconnect all the cables into the proper place.
Bartendro 1 & Bartendro 3 are a cake -- the Raspberry Pi board is easily accessible in the back.

Here is a view of my Bartendro 7's SD Card:

https://www.flickr.com/photos/mayhem/13743267415/

In order to get access to the SD Card, you may need to disconnect a few dispenser cables as I did. Once
you have access to the SD Card, remove the SD Card be sliding it to the right. It should pop right out. But,
be careful! The holder for the SD Card is quite fragile and I've managed to break a Raspberry Pi that way.
Take the existing card and set it aside in some place safe. I would suggest getting a plastic bag if you
don't have an SD Card case handy. Label the bag so you can remember what this SD Card is!

Once you've set aside the old SD Card, insert the newly written SD Card into the SD Card slot in the Raspberry
Pi. Again, be careful to not damage the Raspberry pi. Make sure the card is slid all the way to the left
so that it is seated properly.

Finally, reconnect any dispensers you may have disconnected, taking care to connect the dispensers
back into the appropriate sockets. Refer to the picture you too previously in case you have any questions
as to where each cable should go. Then, turn Bartendro back upright if you turned it upside down. Then connect 
power and boot Bartendro. 

Once Bartendro is up and running, return to your laptop and go back to Bartendro's admin interface and open
the Options page. Ihe Database box, click the red "upload a database" button and follow the instructions to
upload the bartendro.db file that you downloaded earlier. After this Bartendro will reboot and your Bartendro
software update should be complete.

Bartendro is now ready to use again. 

Reporting bugs
--------------

If you find any bugs (issues), please report them here:

https://github.com/partyrobotics/bartendro/issues/new

If you run into trouble during this update, give us a shout here: http://partyrobotics.com/contact-us/

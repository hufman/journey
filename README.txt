This script uses the music data files from the Journey disc. To extract them, extract the PS3_EXTRA/D002/DATA000.PKG file, and copy the 8m3* files from NPUA70218\USRDIR\Data\Sounds\Streams\mus to this directory.

Once there, you can use parse.py to view fun informations about the midi files, including possible transition points.
Mainly, edit the render.py file to specify the progression options. Edit the filetype and fileext settings in defines to indicate the source audio format. Then, edit the call to render at the end to specify what filename and format should be used.


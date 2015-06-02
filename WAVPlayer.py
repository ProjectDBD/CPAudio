import wave

from cpaudio_lib import *

def playback( in_device, in_buffer_length ):                                    
  data = ''

  if( WAVPlayer.wavFile ):
    number_of_frames =    \
      in_buffer_length /  \
      ( WAVPlayer.wavFile.getsampwidth() * WAVPlayer.wavFile.getnchannels() )
  
    data = WAVPlayer.wavFile.readframes( number_of_frames )
  else:
    print "ERROR: WAV file handler is not initialized!"

  return( data )

class WAVPlayer:
  wavFile = None

  def __init__( self, fileName ):
    self.fileName = fileName

  def openWAVFile( self ):
    try:
      WAVPlayer.wavFile = wave.open( self.fileName, "rb" )

      print "WAV file information:"
      print "\tFile:\t\t\t", self.fileName
      print "\tChannels:\t\t", WAVPlayer.wavFile.getnchannels()
      print "\tSample bit depth:\t", WAVPlayer.wavFile.getsampwidth() * 8
      print "\tSample rate:\t\t", WAVPlayer.wavFile.getframerate()
    except wave.Error:
      print "ERROR: Could not open %s for read." %( self.fileName )

  def play( self, device, duration ):
    self.openWAVFile()

    if  (                                         \
      not device.hasAppropriateStream (           \
            CAHAL_DEVICE_OUTPUT_STREAM,           \
            WAVPlayer.wavFile.getnchannels(),     \
            WAVPlayer.wavFile.getsampwidth() * 8, \
            WAVPlayer.wavFile.getframerate()      \
                                      )           \
        ):
      print "WARNING: Could not find an appropriate stream."

    flags =                                   \
      CAHAL_AUDIO_FORMAT_FLAGISSIGNEDINTEGER  \
      | CAHAL_AUDIO_FORMAT_FLAGISPACKED                                                                                

    if( WAVPlayer.wavFile ):
      if  (
        start_playback  (                   \
          device.struct,                    \
          CAHAL_AUDIO_FORMAT_LINEARPCM,     \
          self.wavFile.getnchannels(),      \
          self.wavFile.getframerate(),      \
          self.wavFile.getsampwidth() * 8,  \
          playback,                         \
          flags                             \
                        )                   \
          ):
        cahal_sleep( duration )
      
        cahal_stop_playback()
      else:
        print "ERROR: Could not start playing."
    else:
      print "ERROR: Could not open WAV file."

  def closeWAVFile( self ):
    WAVPlayer.wavFile.close()

    WAVPlayer.wavFile = None

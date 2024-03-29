import wave

from cpaudio_lib import *
  
def saveSignalToWAV (
  signal, outputFileName, numberOfChannels, bitDepth, sampleRate
                      ):
  if( signal ):
    wavWriter = wave.open( outputFileName, "wb" )
        
    wavWriter.setnchannels( numberOfChannels )
    wavWriter.setsampwidth( bitDepth / 8 )
    wavWriter.setframerate( sampleRate )

    data = signal.getRawBytes()

    if( 0 < len( data ) ):
      wavWriter.writeframes( data )

    wavWriter.close()

def bufferSamples( in_device, in_buffer, in_buffer_length ):                         
  if( WAVRecorder.wavFile ):
    WAVRecorder.wavFile.writeframes( in_buffer )
  else:
    print "ERROR: WAV file handler is not initialized!"

class WAVRecorder:
  wavFile = None

  def __init__( self, numberOfChannels, bitDepth, sampleRate ):
    self.numberOfChannels = numberOfChannels
    self.bitDepth         = bitDepth
    self.sampleRate       = sampleRate

  def record( self, device, duration, outputFileName ):
    if  (                               \
      device.hasAppropriateStream (     \
            CAHAL_DEVICE_INPUT_STREAM,  \
            self.numberOfChannels,      \
            self.bitDepth,              \
            self.sampleRate             \
                                  )     \
        ):
      try:
        WAVRecorder.wavFile = wave.open( outputFileName, "wb" )
        
        WAVRecorder.wavFile.setnchannels( self.numberOfChannels )
        WAVRecorder.wavFile.setsampwidth( self.bitDepth / 8 )
        WAVRecorder.wavFile.setframerate( self.sampleRate )
  
        flags =                                   \
          CAHAL_AUDIO_FORMAT_FLAGISSIGNEDINTEGER  \
          | CAHAL_AUDIO_FORMAT_FLAGISPACKED                                                                                
  
        if  (
          start_recording (               \
            device.struct,                \
            CAHAL_AUDIO_FORMAT_LINEARPCM, \
            self.numberOfChannels,        \
            self.sampleRate,              \
            self.bitDepth,                \
            bufferSamples,                \
            flags                         \
                          )               \
            ):
          print "Starting recording..."

          cahal_sleep( duration * 1000 )

          print "Stopping recording..."

          cahal_stop_recording()

          print "Stopped recording."
        else:
          print "ERROR: Could not start recording."
  
        WAVRecorder.wavFile.close()
  
        WAVRecorder.wavFile = None
      except wave.Error:
        print "ERROR: Error while creating WAV file."
    else:
      print "ERROR: Could not find an appropriate stream."


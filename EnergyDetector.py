try:
  import threading as _threading
except ImportError:
  import dummy_threading as _threading

from cpaudio_lib import *

from BitPacker import BitPacker
from BitStream import BitStream

from ascii_graph import Pyasciigraph

import WAVRecorder

import os
import math
import wave
import calendar
import time
import platform
import re

def bufferSamples( in_device, in_buffer, in_buffer_length ):                         
  if( EnergyDetector.bitPacker and EnergyDetector.lock ):
    EnergyDetector.lock.acquire( True )

    EnergyDetector.bitPacker.writeBytes( in_buffer )

    EnergyDetector.lock.release()

    EnergyDetector.semaphore.release()
  else:
    print "ERROR: WAV file handler is not initialized!"

class EnergyDetector:
  bitPacker           = None
  lock                = None
  semaphore           = None
  numObservationBits  = None

  def __init__  (
    self, bitDepth, numberOfChannels, sampleRate, observationInterval,
    firstStopband, firstPassband, secondPassband, secondStopband,
    passbandAttenuation, stopbandAttenuation, outputFileName,
    filter, writeOutput
                ):
    self.signal               = None
    self.bitDepth             = bitDepth
    self.numberOfChannels     = numberOfChannels
    self.sampleRate           = sampleRate
   
    self.firstStopband        = firstStopband
    self.firstPassband        = firstPassband
    self.secondPassband       = secondPassband
    self.secondStopband       = secondStopband

    self.passbandAttenuation  = passbandAttenuation
    self.stopbandAttenuation  = stopbandAttenuation
    
    self.observationInterval  = observationInterval

    self.writeOutput          = writeOutput
    self.applyFilter          = filter

    if( self.writeOutput ):
      self.outputFileName = outputFileName
    else:
      self.outputFileName = None

    if( self.applyFilter ):
      self.filter =  \
        python_initialize_kaiser_filter (
          self.firstStopband,
          self.firstPassband,
          self.secondPassband,
          self.secondStopband,
          self.passbandAttenuation,
          self.stopbandAttenuation,
          int( self.sampleRate )
                                        )
    else:
      self.filter = None

  def detect( self, device, duration ):
    if  (                               \
      device.hasAppropriateStream (     \
            CAHAL_DEVICE_INPUT_STREAM,  \
            self.numberOfChannels,      \
            self.bitDepth,              \
            self.sampleRate             \
                                  )     \
        ):
      flags =                                   \
        CAHAL_AUDIO_FORMAT_FLAGISSIGNEDINTEGER  \
        | CAHAL_AUDIO_FORMAT_FLAGISPACKED                                                                                

      EnergyDetector.bitPacker  = BitPacker()
      EnergyDetector.lock       = _threading.Lock()
      EnergyDetector.semaphore  = _threading.Semaphore( 0 )

      self.signal               = BitStream( EnergyDetector.bitPacker )

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

        self.processObservations( duration )

        print "Stopping recording..."

        cahal_stop_recording()

        print "Stopped recording."
      else:
        print "ERROR: Could not start recording."
    else:
      print "ERROR: Could not find an appropriate stream."

    EnergyDetector.bitPacker  = None
    EnergyDetector.lock       = None
    EnergyDetector.semaphore  = None

  def processObservations( self, duration ):
    numObservations = \
      int( math.ceil( duration / self.observationInterval ) )

    print "Number of observations is 0x%x." %( numObservations )

    numObservationSamples     = \
      int( math.ceil( self.observationInterval * self.sampleRate ) )
    numObservationBits        =  \
      numObservationSamples * self.numberOfChannels * self.bitDepth
    numProcessedObservations  = 0
    graphPeriod               = 1.0 / self.observationInterval

    if( graphPeriod < 0 ):
      graphPeriod = 1

    print "Observation bits: %d." %( numObservationBits )

    while( numProcessedObservations < numObservations ):
      part = []

      EnergyDetector.lock.acquire( True )

      availableData = self.signal.getSize()

      EnergyDetector.lock.release()

      if( availableData >= numObservationBits ):
        numProcessedObservations += 1

        EnergyDetector.lock.acquire( True )

        buffer = self.signal.read( numObservationBits )

        EnergyDetector.lock.release()

        bufferedSamples = BitStream( buffer )

        for sampleIndex in range( numObservationSamples ):
          sampleValue = bufferedSamples.read( self.bitDepth )            

          for channelIndex in range( self.numberOfChannels - 1 ):
            bufferedSamples.read( self.bitDepth )

          part.append( sampleValue * 1.0 )

        if( 0 < len( part ) ):
          if( self.applyFilter ):
            part = python_filter_signal( self.filter, part )

          if( 0 == ( numProcessedObservations % int( graphPeriod ) ) ):
            self.graphFFT( part )
  
          self.calculateEnergy( part )
      else:
        EnergyDetector.semaphore.acquire( True )

  def calculateEnergy( self, signal ):
    energy = 0
    
    for sample in signal:
      energy += sample ** 2 

    print "Energy: %.02f dB" %( 10 * math.log10( energy ) )

  def graphFFT( self, signal ):
    fft     = python_calculate_FFT( signal )
    fftMag  = map( lambda x: abs( x ), fft )

    N         = len( fftMag )
    delta     = 1.0 / self.sampleRate
    maxValue  = -1

    for magnitude in fftMag:
      if( magnitude > maxValue ):
        maxValue = magnitude

    fftMag = map( lambda x: 10**-12 if x == 0 else x, fftMag )
    fftMag = map( lambda x: 10 * math.log10( x / maxValue ), fftMag )

    graphLabel  = "Observation FFT (%.02f sec)" %( self.observationInterval )
    dataPoints  = []

    for n in range( int( N / 2 ) ):
      frequency = n / ( delta * N )

      label = "%.02f Hz" %( frequency )

      if( self.applyFilter ):
        if  (
          frequency >= self.firstStopband
          and frequency <= self.secondStopband
            ):
          dataPoints.append( ( frequency, fftMag[ n ] ) )
      else:
        dataPoints.append( ( frequency, fftMag[ n ] ) )

    dataPoints  = self.decimate( dataPoints )
    graph       = Pyasciigraph()
    plot        = graph.graph( graphLabel, dataPoints )

    self.clearScreen()

    for line in plot:
      print(line)

  def clearScreen( self ):
    platform = self.determinePlatform()

    if( platform == "Windows" ):
      os.system( 'cls' )
    else:
      os.system( 'clear' )

  def decimate( self, dataPoints ):
    numSubPoints = len( dataPoints ) / 40

    numGroups = int( math.ceil( len( dataPoints ) / numSubPoints ) )

    decimatedPoints = []

    for groupIndex in range( numGroups ):
      averageFrequency  = 0
      averageMagnitude  = 0

      for pointIndex in range( numSubPoints ):
        index = groupIndex * numSubPoints + pointIndex

        ( frequency, magnitude ) = dataPoints[ index ] 

        averageFrequency += frequency
        averageMagnitude += magnitude

      averageFrequency /= numSubPoints
      averageMagnitude /= numSubPoints

      label = "%d Hz" %( int( averageFrequency ) )
      point = int( abs( averageMagnitude ) )

      decimatedPoints.append( ( label, point ) )

    return( decimatedPoints )

  def __del__( self ):
    if( self.writeOutput ):
      WAVRecorder.saveSignalToWAV ( 
        self.signal, self.outputFileName, self.numberOfChannels,
        self.bitDepth, self.sampleRate
                                  )

    if( self.signal ):
      self.signal = None

    if( self.filter ):
      csignal_destroy_passband_filter( self.filter )

    EnergyDetector.bitPacker           = None
    EnergyDetector.lock                = None
    EnergyDetector.semaphore           = None
    EnergyDetector.numObservationBits  = None

  def determinePlatform( self ):
    platform_info = platform.uname()

    iphone_re = re.compile( "^iPhone", re.IGNORECASE )
    
    if( platform_info[ 0 ] == "Darwin" ):
      if( iphone_re.search( platform_info[ 4 ] ) ):
        return( "iPhone" )
      else:
        return( "Mac OSX" )
    elif( platform_info[ 0 ] == "Linux" ):
      return( "Android" )
    elif( platform_info[ 0 ] == "Windows" ):
      return( "Windows" )


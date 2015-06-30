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
  if( BaseRecorder.bitPacker and BaseRecorder.lock ):
    BaseRecorder.lock.acquire( True )

    BaseRecorder.bitPacker.writeBytes( in_buffer )

    BaseRecorder.lock.release()

    BaseRecorder.semaphore.release()
  else:
    print "ERROR: Packer and lock are not initialized!"

class BaseRecorder:
  bitPacker           = None
  lock                = None
  semaphore           = None
  numObservationBits  = None

  def __init__  (
    self, bitDepth, numberOfChannels, sampleRate, widebandFirstStopband,
    widebandFirstPassband, widebandSecondPassband, widebandSecondStopband,
    passbandAttenuation, stopbandAttenuation, outputFileName, filter,
    writeOutput
                ):
    self.signal                 = None
    self.bitDepth               = bitDepth
    self.numberOfChannels       = numberOfChannels
    self.sampleRate             = int( sampleRate )
   
    self.widebandFirstStopband  = widebandFirstStopband
    self.widebandFirstPassband  = widebandFirstPassband
    self.widebandSecondPassband = widebandSecondPassband
    self.widebandSecondStopband = widebandSecondStopband

    self.passbandAttenuation    = passbandAttenuation
    self.stopbandAttenuation    = stopbandAttenuation

    self.writeOutput            = writeOutput
    self.applyFilter            = filter

    if( self.writeOutput ):
      self.outputFileName = outputFileName
    else:
      self.outputFileName = None

    if( self.applyFilter ):
      self.widebandFilter =  \
        python_initialize_kaiser_filter (
          self.widebandFirstStopband,
          self.widebandFirstPassband,
          self.widebandSecondPassband,
          self.widebandSecondStopband,
          self.passbandAttenuation,
          self.stopbandAttenuation,
          int( self.sampleRate )
                                        )
    else:
      self.widebandFilter = None

  def record( self, device ):
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

      BaseRecorder.bitPacker  = BitPacker()
      BaseRecorder.lock       = _threading.Lock()
      BaseRecorder.semaphore  = _threading.Semaphore( 0 )

      self.signal             = BitStream( BaseRecorder.bitPacker )

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

        self.processObservations()

        print "Stopping recording..."

        cahal_stop_recording()

        print "Stopped recording."
      else:
        print "ERROR: Could not start recording."
    else:
      print "ERROR: Could not find an appropriate stream."

    BaseRecorder.bitPacker  = None
    BaseRecorder.lock       = None
    BaseRecorder.semaphore  = None

  def processObservations( self ):
    done = False

    while( not done ):
      buffer = None

      nBitsToRead = self.getNumberOfBitsToRead()

      BaseRecorder.semaphore.acquire( True )

      BaseRecorder.lock.acquire( True )

      availableData = self.signal.getSize()

      BaseRecorder.lock.release()

      #print "Available %d, waiting for %d." %( availableData, nBitsToRead )

      while( availableData >= nBitsToRead and not done ):
        BaseRecorder.lock.acquire( True )

        buffer = self.signal.read( nBitsToRead )

        BaseRecorder.lock.release()

        if( None != buffer ):
          done = self.processBuffer( buffer )

        nBitsToRead = self.getNumberOfBitsToRead()

        BaseRecorder.lock.acquire( True )

        availableData = self.signal.getSize()

        BaseRecorder.lock.release()

        #print "Available %d, waiting for %d." %( availableData, nBitsToRead )

  def getNumberOfBitsToRead( self ):
    return( 0 )

  def processbuffer( self, buffer ):
    return( True )

  def __del__( self ):
    if( self.writeOutput ):
      WAVRecorder.saveSignalToWAV ( 
        self.signal, self.outputFileName, self.numberOfChannels,
        self.bitDepth, self.sampleRate
                                  )

    if( self.signal ):
      self.signal = None

    if( self.widebandFilter ):
      csignal_destroy_passband_filter( self.widebandFilter )

    BaseRecorder.bitPacker           = None
    BaseRecorder.lock                = None
    BaseRecorder.semaphore           = None
    BaseRecorder.numObservationBits  = None

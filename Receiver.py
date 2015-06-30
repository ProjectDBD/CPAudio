from cpaudio_lib import *

from BitPacker import BitPacker
from BitStream import BitStream
from BaseRecorder import BaseRecorder

from ascii_graph import Pyasciigraph

import os
import math
import wave
import calendar
import time
import platform
import re
import struct

class Receiver( BaseRecorder ):
  MULTIPLIER = 3

  def __init__  (
    self, bitDepth, numberOfChannels, sampleRate, bitsPerSymbol,
    samplesPerSymbol, carrierFrequency, widebandFirstStopband,
    widebandFirstPassband, widebandSecondPassband, widebandSecondStopband,
    narrowbandFirstStopband, narrowbandFirstPassband,
    narrowbandSecondPassband, narrowbandSecondStopband, passbandAttenuation,
    stopbandAttenuation,  polynomialDegree, firstGenerator, secondGenerator,
    firstInitialValue, secondInitialValue, samplesPerChip,
    numberOfTrainingSymbols, outputFileName, writeOutput, duration
                ):

    BaseRecorder.__init__  (
      self, bitDepth, numberOfChannels, sampleRate, widebandFirstStopband,
      widebandFirstPassband, widebandSecondPassband, widebandSecondStopband,
      passbandAttenuation, stopbandAttenuation, outputFileName, True,
      writeOutput
                          )

    self.bitsPerSymbol            = bitsPerSymbol
    self.samplesPerSymbol         = samplesPerSymbol
    self.samplesPerChip           = samplesPerChip
    self.carrierFrequency         = carrierFrequency
    self.numberOfTrainingSymbols  = numberOfTrainingSymbols
    self.constellationSize        = 2 ** bitsPerSymbol
    self.basebandAmplitude        = 2 ** ( self.bitDepth - 1 ) - 1

    self.inphaseCode              = \
      python_initialize_gold_code (
        polynomialDegree, firstGenerator, secondGenerator,
        firstInitialValue, secondInitialValue
                                  )

    self.quadratureCode           = \
      python_initialize_gold_code (
        polynomialDegree, firstGenerator, secondGenerator,
        firstInitialValue, secondInitialValue
                                  )

    self.initializeReferenceSpreadingCode()

    self.numObservationBits       =                                     \
      len( self.spreadingCode ) * self.numberOfChannels * self.bitDepth \
      * Receiver.MULTIPLIER

    self.maxNumberOfObservations  = \
      math.ceil (
        ( duration * self.sampleRate )
        / ( ( self.numObservationBits * 1.0 ) / 8.0 )
                )

    print "Max number of observations: %d." %( self.maxNumberOfObservations )

    self.numProcessedObservations = 0

    self.narrowbandFilter         =  \
      python_initialize_kaiser_filter (
        narrowbandFirstStopband,
        narrowbandFirstPassband,
        narrowbandSecondPassband,
        narrowbandSecondStopband,
        passbandAttenuation,
        stopbandAttenuation,
        int( self.sampleRate )
                                      )   

  def getNumberOfBitsToRead( self ):
    print "Number of observation bits is %d." %( self.numObservationBits )

    return( self.numObservationBits )

  def processBuffer( self, buffer ):
    done = False

    print "Processing buffer, length is %d." %( len( buffer ) )

    if( len( buffer ) * 8 < self.numObservationBits ):
      print "ERROR: Received an incomplete buffer (%d), expexting (%d)" \
        %( ( len( buffer ) * 8 ), self.numObservationBits )

      done = True
    else:
      self.numProcessedObservations += 1

      print "nProcessed=%d." %( self.numProcessedObservations )

      done = ( self.numProcessedObservations >= self.maxNumberOfObservations )

    return( done )

  def initializeReferenceSpreadingCode( self ):
    nBytes = \
      int (
        math.ceil (
          ( self.numberOfTrainingSymbols * self.bitsPerSymbol * 1.0 ) / 8.0
                  )
          )

    data = '\x00' * nBytes 
    
    tracker = python_bit_stream_initialize( data )

    ( numberOfBits, buffer ) = \
      python_bit_stream_get_bits( tracker, self.bitsPerSymbol ) 

    symbol = struct.unpack( "B", buffer )[ 0 ]

    self.spreadingCode = []

    while( symbol != None ):
      components = python_modulate_symbol (
          symbol,
          self.constellationSize,
          self.sampleRate,
          self.samplesPerSymbol,
          self.basebandAmplitude,
          self.carrierFrequency
                                          )
  
      I = python_spread_signal (
          self.inphaseCode,
          self.samplesPerChip,
          components[ 0 ]
                                          )

      Q = python_spread_signal  (
          self.quadratureCode,
          self.samplesPerChip,
          components[ 1 ]
                                )

      part = []

      for index in range( self.samplesPerSymbol ):
        sampleValue = I[ index ] - Q[ index ]

        part.append( sampleValue )

      self.spreadingCode = self.spreadingCode + part

      ( numberOfBits, buffer ) = \
        python_bit_stream_get_bits( tracker, self.bitsPerSymbol ) 

      if( 0 == numberOfBits ):
        symbol = None
      else:
        symbol = struct.unpack( "B", buffer )[ 0 ] 

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

    testsPerChip                  = 1
    self.decimationFactor         = int( self.samplesPerChip / testsPerChip )

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
        / (
            self.samplesPerSymbol * self.numberOfTrainingSymbols
            * Receiver.MULTIPLIER
          )
                )

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
    return( self.numObservationBits )

  def processBuffer( self, buffer ):
    done = False

    if( len( buffer ) * 8 < self.numObservationBits ):
      print "ERROR: Received an incomplete buffer (%d), expexting (%d)" \
        %( ( len( buffer ) * 8 ), self.numObservationBits )

      done = True
    else:
      part            = []
      bufferedSamples = BitStream( buffer )

      numObservationSamples = len( self.spreadingCode ) * Receiver.MULTIPLIER

      for sampleIndex in range( numObservationSamples ):
        sampleValue = bufferedSamples.read( self.bitDepth )            

        for channelIndex in range( self.numberOfChannels - 1 ):
          bufferedSamples.read( self.bitDepth )

        sampleValue = struct.pack( "!I", sampleValue )
        sampleValue = struct.unpack( "i", sampleValue )[ 0 ]

        part.append( sampleValue * 1.0 )

      if( part != None and 0 < len( part ) ):
        self.detectTrainingSequence( part )

      self.numProcessedObservations += 1

      done = ( self.numProcessedObservations >= self.maxNumberOfObservations )

    return( done )

  def detectTrainingSequence( self, signal ):
    thresholds =  \
      python_csignal_calculate_thresholds ( 
        self.spreadingCode,
        self.widebandFilter,
        self.narrowbandFilter,
        signal,
        self.decimationFactor
                                          )

    max = 0

    for threshold in thresholds:
      if( threshold > max ):
        max = threshold

    print "Max threshold is %.04f dB" %( 10 * math.log10( max ) )

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

    nSymbols  = 0
    symbol    = struct.unpack( "B", buffer )[ 0 ]

    self.spreadingCode = []

    while( symbol != None and nSymbols < self.numberOfTrainingSymbols ):
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

      nSymbols += 1

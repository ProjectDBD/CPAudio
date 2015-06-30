from cpaudio_lib import *

from BitPacker import BitPacker
from BitStream import BitStream
from BaseRecorder import BaseRecorder

from ascii_graph import Pyasciigraph

import WAVRecorder

import struct
import os
import math
import wave
import calendar
import time
import platform
import re

class EnergyDetector( BaseRecorder ):
  def __init__  (
    self, bitDepth, numberOfChannels, sampleRate, observationInterval,
    widebandFirstStopband, widebandFirstPassband, widebandSecondPassband,
    widebandSecondStopband, passbandAttenuation, stopbandAttenuation,
    outputFileName, filter, writeOutput, duration
                ):

    BaseRecorder.__init__  (
      self, bitDepth, numberOfChannels, sampleRate, widebandFirstStopband,
      widebandFirstPassband, widebandSecondPassband, widebandSecondStopband,
      passbandAttenuation, stopbandAttenuation, outputFileName, filter,
      writeOutput
                          )

    self.observationInterval      = observationInterval
    self.duration                 = duration
    self.numObservations          = \
      int( math.ceil( self.duration / self.observationInterval ) )
    self.numObservationSamples    = \
      int( math.ceil( self.observationInterval * self.sampleRate ) )
    self.numObservationBits       =  \
      self.numObservationSamples * self.numberOfChannels * self.bitDepth
    self.numProcessedObservations = 0
    self.graphPeriod              = 1.0 / self.observationInterval

    if( self.graphPeriod < 0 ):
      self.graphPeriod = 1

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

      for sampleIndex in range( self.numObservationSamples ):
        sampleValue = bufferedSamples.read( self.bitDepth )            

        for channelIndex in range( self.numberOfChannels - 1 ):
          bufferedSamples.read( self.bitDepth )

        sampleValue = struct.pack( "!I", sampleValue )
        sampleValue = struct.unpack( "i", sampleValue )[ 0 ]

        part.append( sampleValue * 1.0 )

      if( 0 < len( part ) ):
        if( self.applyFilter ):
          part = python_filter_signal( self.widebandFilter, part )

        if( 0 == ( self.numProcessedObservations % int( self.graphPeriod ) ) ):
          self.graphFFT( part )
  
        self.calculateEnergy( part )     

      self.numProcessedObservations += 1

      done = ( self.numProcessedObservations >= self.numObservations )

    return( done )

  def calculateEnergy( self, signal ):
    energy = python_csignal_calculate_energy( signal )

    print "Energy: %.02f dB" %( 10 * math.log10( energy ) )

  def graphFFT( self, signal ):
    fft     = python_calculate_FFT( signal )
    fftMag  = map( lambda x: abs( x ), fft )

    N         = len( fftMag )
    delta     = 1.0 / self.sampleRate

    maxValue  = -1

    for magnitude in fftMag[ 1 : len( fftMag ) ]:
      if( magnitude > maxValue ):
        maxValue = magnitude

    fftMag = map( lambda x: 10**-12 if x == 0 else x, fftMag )
    fftMag = map( lambda x: 10 * math.log10( x / maxValue ), fftMag )

    graphLabel  = "Observation FFT (%.02f sec)" %( self.observationInterval )
    dataPoints  = []

    for n in range( 1, int( N / 2 ) ):
      frequency = n / ( delta * N )

      label = "%.02f Hz" %( frequency )

      if( self.applyFilter ):
        if  (
          frequency >= self.widebandFirstPassband
          and frequency <= self.widebandSecondPassband
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


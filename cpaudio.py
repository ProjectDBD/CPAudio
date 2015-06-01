from cpaudio_lib import *

import argparse

parser        = None
args          = None
list_devices  = None

def setup():
  global parser
  global args 
  global list_devices

  cahal_initialize()

  parser =                                                        \
    argparse.ArgumentParser (                                     \
      description='Interact with the platform\'s audio hardware'  \
                            )

  parser.add_argument (           \
    '-l',                         \
    '--list-devices',             \
    action='store_true',          \
    dest='list_devices',          \
    help='List all audio devices' \
                      )

  parser.add_argument (                                                 \
    '-v',                                                               \
    '--verbosity',                                                      \
    choices = [ 'trace', 'debug', 'info', 'warning', 'error', 'none' ], \
    action = 'store',                                                   \
    default = 'error',                                                  \
    dest = 'verbosity',                                                 \
    help = 'Verbosity level'                                            \
                      )

  args = parser.parse_args()


def terminate():
  cahal_terminate()

def initialize_debug_info():
  global args

  if( args.verbosity == 'trace' ):
    cpc_log_set_log_level( CPC_LOG_LEVEL_TRACE )
  elif( args.verbosity == 'debug' ):
    cpc_log_set_log_level( CPC_LOG_LEVEL_DEBUG )
  elif( args.verbosity == 'info' ):
    cpc_log_set_log_level( CPC_LOG_LEVEL_INFO )
  elif( args.verbosity == 'warning' ):
    cpc_log_set_log_level( CPC_LOG_LEVEL_WARNING )
  elif( args.verbosity == 'error' ):
    cpc_log_set_log_level( CPC_LOG_LEVEL_ERROR )
  elif( args.verbosity == 'none' ):
    cpc_log_set_log_level( CPC_LOG_LEVEL_NO_LOGGING )
  else:
    args.print_usage()

def print_device( device ):
  print "Device '%s'" %( device.device_name )

  if( device.model ):
    print "\tModel: %s" %( device.model ) 
  if( device.manufacturer ):
    print "\tManufacturer: %s" %( device.manufacturer ) 
  if( device.serial_number ):
    print "\tSN: %s" %( device.serial_number )
  if( device.version ):
    print "\tVersion: %s" %( device.version )
  if( device.device_uid ):
    print "\tUID: %s" %( device.device_uid )
  if( device.model_uid ):
    print "\tModel UID: %s" %( device.model_uid )
   
  print "\tAlive?: %s" %( "Yes" if device.is_alive else "No" )
  print "\tRunning?: %s" %( "Yes" if device.is_running else "No" )

  if( device.preferred_number_of_channels and device.preferred_sample_rate ):
    print "\tPreferences:"
    print "\t\t%d channel(s), %.02f Hz" \
      %( device.preferred_number_of_channels, device.preferred_sample_rate )

  if( device.supported_sample_rates ):
    sample_rate_index = 0
    sample_rate       =                   \
      cahal_sample_rate_range_list_get  ( \
        device.supported_sample_rates,    \
        sample_rate_index                 \
                                        )
    
    print "\tSupported sample rates:"

    while( sample_rate ):
      if( sample_rate.mininum_rate != sample_rate.maximum_rate ):
        print "\t\t%d Hz - %d Hx" \
          %( sample_rate.minimum_rate, sample_rate.maximum_rate )
      else:
        print "\t\t%d Hz" %( sample_rate.minimum_rate )

      sample_rate_index += 1

      sample_rate =                         \
        cahal_sample_rate_range_list_get  ( \
          device.supported_sample_rates,    \
          sample_rate_index                 \
                                          )

  if( device.device_streams ):    
    stream_index  = 0                                                             
    stream        =                   \
      cahal_device_stream_list_get  ( \
        device.device_streams,        \
        stream_index                  \
                                    )

    print "\tStreams:"

    while( stream ):
      print "\t\tDirection: %s"                             \
        %(                                                  \
          "Input"                                           \
          if stream.direction == CAHAL_DEVICE_INPUT_STREAM  \
          else "Output"                                     \
        )

      if( stream.preferred_format ):
        print "\t\tPreferred format: %s"                \
          %(                                            \
            cahal_convert_audio_format_id_to_cstring  ( \
              stream.preferred_format                   \
                                                      ) \
          )

      if( stream.supported_formats ):
        print "\t\tSupported formats:"

      format_description_index  = 0
      format_description        =                 \
        cahal_audio_format_description_list_get ( \
          stream.supported_formats,               \
          format_description_index                \
                                                )

      while( format_description ):
        print "\t\t\t%s, %d channel(s), %d bits, %.02f Hz"      \
          %(                                                    \
            cahal_convert_audio_format_id_to_cstring  (         \
              format_description.format_id                      \
                                                      ),        \
            format_description.number_of_channels,              \
            format_description.bit_depth,                       \
            format_description.sample_rate_range.minimum_rate   \
          )

        format_description_index  += 1 
        format_description        =                 \
          cahal_audio_format_description_list_get ( \
            stream.supported_formats,               \
            format_description_index                \
                                                  )

      stream_index += 1
      stream        =                   \
        cahal_device_stream_list_get  ( \
          device.device_streams,        \
          stream_index                  \
                                      )

setup()

initialize_debug_info()

if( args.list_devices ):
  device_list = cahal_get_device_list()
  index       = 0                                                             
  device      = cahal_device_list_get( device_list, index )       
                                                                               
  while( device ):
    print_device( device )

    index   += 1                                                              
    device  = cahal_device_list_get( device_list, index )
else:
  parser.print_help()

terminate()

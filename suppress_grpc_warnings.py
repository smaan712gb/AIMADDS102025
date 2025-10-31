"""
Suppress gRPC ALTS warnings when running outside Google Cloud Platform

Add this at the top of your main scripts to suppress harmless gRPC warnings.
"""
import os
import warnings
import logging

def suppress_grpc_warnings():
    """
    Suppress gRPC ALTS credential warnings.
    
    These warnings appear when using Google AI services (Gemini) outside of GCP.
    They are harmless and don't affect functionality.
    """
    # Suppress gRPC warnings via environment variables
    os.environ['GRPC_VERBOSITY'] = 'ERROR'
    os.environ['GRPC_TRACE'] = ''
    
    # Suppress Python warnings
    warnings.filterwarnings('ignore', category=UserWarning, module='google')
    warnings.filterwarnings('ignore', message='.*ALTS.*')
    
    # Configure gRPC logging
    logging.getLogger('grpc').setLevel(logging.ERROR)
    logging.getLogger('google').setLevel(logging.ERROR)
    logging.getLogger('google.auth').setLevel(logging.ERROR)
    logging.getLogger('google.api_core').setLevel(logging.ERROR)

# Usage: Add to the top of production_crwd_analysis.py:
# from suppress_grpc_warnings import suppress_grpc_warnings
# suppress_grpc_warnings()

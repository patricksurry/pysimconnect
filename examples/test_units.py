from simconnect import SimConnect

# The SDK will automatically convert simulation variables to compatible units

with SimConnect() as sc:
    print("Fetching Indicated Altitude with various units")
    print("default (Feet inferred)",  sc.get_simdatum("Indicated Altitude"))
    # These are defined explicitly as units by the SDK
    print("Feet",  sc.get_simdatum("Indicated Altitude", units="Feet"))
    print("Foot",  sc.get_simdatum("Indicated Altitude", units="Foot"))
    # Case insensitive?
    print("feet",  sc.get_simdatum("Indicated Altitude", units="feet"))
    print("FEET",  sc.get_simdatum("Indicated Altitude", units="FEET"))
    # Alternative length units
    print("meters",  sc.get_simdatum("Indicated Altitude", units="meters"))
    print("m",  sc.get_simdatum("Indicated Altitude", units="m"))
    # Explicitly empty
    print("empty ('')", sc.get_simdatum("Indicated Altitude", units=""))

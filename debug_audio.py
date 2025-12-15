import soundcard as sc

try:
    spk = sc.default_speaker()
    print(f"Default Speaker: {spk.name}")
    # Try to connect without specifying rate to see what it defaults to? 
    # Actually soundcard doesn't expose 'samplerate' property easily on the object without opening it,
    # but let's try opening it and seeing if we can inspect or just check documentation.
    # Wait, usually we just assume a standard one.
    
    # Let's try to find the loopback mic and see its properties
    mics = sc.all_microphones(include_loopback=True)
    loopback = None
    for m in mics:
        if m.isloopback and spk.name in m.name:
            loopback = m
            break
            
    if not loopback:
        # Fallback search
        for m in mics:
            if m.isloopback:
                loopback = m
                break
                
    if loopback:
        print(f"Loopback Device: {loopback.name}")
        # There is no direct .samplerate property on Microphone object in soundcard 0.4
        # We have to guess or try recording.
    else:
        print("No loopback found")

except Exception as e:
    print(e)

pyspy - Python gamespy client

Usage:

    import pyspy
    client = pyspy.GamespyClient("s.camin.us", 25566)
    client.update()
    print client.players()
    print client.tags()

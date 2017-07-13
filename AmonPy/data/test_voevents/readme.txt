Here's three events to quickly test the amonpy's real time settings.

When running the client server (both local and ssl versions), you must specify the path (-epath argument) to where the events are located. So to use these tests events have the client point to this directory. 

Once the DB is set up, celery and the twisted serverpost plugin are running you can start up the client post plugin with -path pointing here. 

Once these 3 events are sent by the client post plugin, these things should have succesfully happened,

- All three events should be written to the event table in the DB (2 icecube events, 1 auger event)

- There should be an alert in the Alert table of the DB (coincident between the auger event and one of the IC events).

- The Alert Voevent from the coincident should be written to the alert directory

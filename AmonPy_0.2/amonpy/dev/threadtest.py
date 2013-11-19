#threadtest.py
"""@package threadtest
use multiprocessing module. Similar to threading module but does not
 automatically share data between threads, using instead "message passing" 
 which is implemented here as a "pipe"
""" 
import multiprocessing

# here is the server software, a small analysis that buffers up to Nmax events
# and returns the summed times of the buffer...
def anal(pipe,Nmax):
    server_p,client_p = pipe
    client_p.close()   # close the client pipe on the server
    while True:
        try:
            t=server_p.recv()
        except EOFError:
            break
        try:
            Nbuffer = len(buffer)
        except:
            buffer = []
            Nbuffer = 0
        buffer += [t]
        Nbuffer = len(buffer)
        if Nbuffer > Nmax:
            buffer.pop(0)
        if Nbuffer != 0:
            diff = max(buffer) - min(buffer)
        else:
            diff = 0
        tot  = sum(buffer)
        result = (diff,tot)
        server_p.send(result)
    # Shutdown
    print ("Server done")


# main program here....
if __name__ == '__main__':

    #make a list of "times"
    N = int(30)
    times = [ii for ii in xrange(N)]

    # Launch the sever process
    (server_p,client_p) = multiprocessing.Pipe()
    Nmax = 5
    anal_p = multiprocessing.Process(target=anal,
                                     args=((server_p,client_p),Nmax))
    anal_p.start()

    #loop over the list of times, calling analysis for each
    for t in times:
        client_p.send(t)
        s = (client_p.recv())
        print 'New event time: ', t, ', buffer diff: ', s[0], \
            ', buffer sum: ', s[1]

    #Close the server pipe in the client
    server_p.close()

    #Done. Close the pipe
    client_p.close()

    #wait for consumer process to shutdown
    #anal_p.join()







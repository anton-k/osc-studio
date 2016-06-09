import argparse

parser = argparse.ArgumentParser(description="UI for flow audio server.")
parser.add_argument('--portin', dest='port_in', type=int, nargs='?', help = 'OSC input port')
parser.add_argument('--portout', dest='port_out', type=int, nargs='?', help = 'OSC output port')
parser.add_argument('--path', dest='path', type=str, nargs='?', help = 'Path to load.')

args = parser.parse_args()
print "in: %d, out: %d, path: %s" % (args.port_in, args.port_out, args.path)

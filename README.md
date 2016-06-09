Geek Studio
========================

The Geek Studio (GS) is a collection of utilities to 
play audio samples live. The main principle of the tools is
to keep things modular and control everything with OSC-messages.

Each module consists of an audio server that expects OSC messages (written in Csound),
python client to make interaction with server as easy as possible and
UI to control the server. We can control the UI with OSC.

Right now there are several modules:

* flow -- to play continuous everlasting pads

* sampler -- to play audio files with rhythm

* rnd_tap -- to trigger audio samples at random

Dependencies
---------------------------

We need several tools to run the modules. We need a csound audio language,
python and several python libs: pyOSC, python-csound, wxPython.

Let's look at each of the module


Flow
---------------------------

A tool to play continuous pads. It has several channels as mixing console.
We can start continuous loop on the channel. It's played with crossfade
so that the end of the loop is xfaded with the start of the next loop.
We can start a next audio wave on the channel by sending a message with
the file name. On receive the loop with previous audio file
is xfaded with the next audio file. We can adjust the volume for each channel.

The audio server is encoded in the file flow.csd. We can start a server with csound:

~~~
> csound --omacro:PORT=7700 --omacro:SIZE=8 flow.csd 
~~~

The server expects two arguments to be set. They are `PORT` and `SIZE`.
The server listens on the given `PORT` and has `SIZE` channels.
When server is launched we can start to send OSC-messages.
Let's list the messages:

* `"/play" (channel : int, file_name : string)`
 
    We can start playing a loop on the given channel.
    The file_name can be a mono or stereo wav file or stereo mp3 file.

* `"/stop" (channel : int)`

    We can stop a loop on the give channel.


* `"/resume" (channel : int)`

    We can resume playing.

* `"/set_volume" (channel : int, volume : float)`

    We can set the volume for the given channel.

* `"/set_fade"  (fade_time : float)`

    We can set the fade time for all channels.


There is a python OSC-client that makes sending messages to `flow.csd` very easy.
It's encoded in the `flow.py` module.

Let's start the audio erver on the port 7700 with size 16:

~~~
> csound --omacro:PORT=7700 --omacro:SIZE=16 flow.csd 
~~~

Let's create a flow-client:

~~~
> python
> from flow import *
> c = Flow(port = 7700, size = 16)
~~~

Now we can start playing a loop on the the first and third channels:

~~~
> c.play(0, "saima-breath.wav")
> c.play(2, "ethereal.wav")
~~~

Then we can adjust the volume:

~~~
> c.set_volume(2, 0.65)
> c.stop(0)
~~~

Also we can stop and resume with lists:

~~~
> c.resume([0,2,3])
> c.set_fade(2.5)
~~~

Sampler
-----------------------------------

With sampler we can play a bunch of files with the given tempo.
We can easily adjust the tempo of the files. If you are a Csounder
you will be glad to recognize a mincer in disguise.

We have several channels to play audio files also we have
several memory slots to save the files. It's slightly more involved 
then with `flow`-synt. But with flow we make no transformation on samples.
We play them just as they are adding a bit of xfade. But with sampler
it's a different story. We need to rescale the audio sample to fit
to the tempo net.

Let's start the audio server on the port 7700 with channel size 16 and 32 memmory slots:

~~~
> csound --omacro:PORT=7700 --omacro:SIZE=16 --omacro:MEMORY_SIZE=32 sampler.csd
~~~

We can load audio files to slots and play them at the given tempo.
Also we can change the speed of the playback without changing the pitch.
Here is the OSC-based API:

* `"/load" (slot_id : int, file : string, bpm : float, is_drum : int)`

    Loads an audio `file` to memory slot with gibven `id`. We have to provide
    the audio file `bpm`-rate and say is it a drum. If it's a drum then `is_drum`
    equals to `1` otherwise to `0`.

    We can not load to slot if it's currently in use (is played on some channel).
    We have to stop the playback for the file on the slot first.

* `"/play" (channel : int, slot : int)`

    Starts to play the file in the `slot` on the `channel`.

* `/stop (channel : int)` 

    Stops playback on the given channel

* `/resume (channel : int)` 

    Resumes playback on the given channel

* `set_volume (channel : int, volume : float)` 

    Sets the volume (0 to 1) for the channel

* `set_speed (channel : int, speed : float)` 

    Sets the speed for the channel. The negative
    speed means playing in reverse. Zero speed means stopping the playback.

* `set_length (channel : int, length : int)` -- TOODO

    Sets the length of the synchronization in metromome ticks.
    Everytime we change speed or start/stop sample the action
    comes to effect only when certain amount of metronome ticks 
    is passed. This way we can keep samples adjusted by the first beat.    
    Some samples are allowed to change every 16 ticks (the two bars)
    while another ones are allowed to change every 8 ticks (single bar).
    The default amount is 8 ticks.

* `set_tempo (bpm : float)` 

    Sets the tempo of playback in BPM.

There is a python OSC-client that makes sending messages to `sampler.csd` very easy.
It's encoded in the `sampler.py` module.

Let's start the audio erver on the port 7700 with size 16:

~~~
> csound --omacro:PORT=7700 --omacro:SIZE=16 --omacro:MEMORY_SIZE=16 sampler.csd 
~~~

Let's create a sampler-client:

~~~
> python
> from sampler import *
> c = Sam(port = 7700)
~~~

Lets' load the samples first:

~~~
> bpm =  120
> drums = ['kick.wav', 'snare.wav', 'hi-hat.wav', 'toms.wav']
> instrs = ['piano.wav', 'violins.wav', 'guitar.wav']
> ix = 0
>
> for file in drums:
>    c.load(ix, file, bpm, is_drum = True)
>    ix += 1
>
> for file in instrs:
>    c.load(ix, file, bpm, is_drum = False)
>    ix += 1
>
~~~

Let's play the samples:

~~~
> for i in range(len(drums + instrs)):
>   c.play(i, i)
~~~

Let's set the volume for some of the instruments:

~~~
> c.set_volume([0, 2, 3], 0.57)
~~~

Let's play some of the instruments backwards:

~~~
> c.set_volume([4, 5], -1)
~~~

Random playback of the audio files
---------------------------------------

Sometimes it's cool to play audio files at random. 
We can load some samples and the trigger them all of a sudden.


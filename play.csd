<CsoundSynthesizer>
<CsOptions>
-odac   -d 
</CsOptions>
<CsInstruments>

sr = 44100
ksmps = 64
nchnls = 2
0dbfs  = 1

#ifndef PORT
    #define PORT        # 7700 #
#end

gSFile   = "abracadabra"
gihandle OSCinit $PORT

instr   1
    SFile = ""
    kFadeTime init 0
    kVolume   init 0
    kk init 0

nxtmsg:
    kk  OSClisten gihandle, "/flow/play", "sf", SFile, kFadeTime
if (kk == 0) goto ex
    printks SFile, 0
    gSFile strcpyk SFile
    printks gSFile, 0
    event "i", 100, 0, 5
    kgoto nxtmsg
ex:       
endin

instr 100
    al, ar  diskin2 gSFile, 1
    outs al, ar    
endin

</CsInstruments>
<CsScore>

f0 1000000

i 1 0 -1
e
</CsScore>
</CsoundSynthesizer>

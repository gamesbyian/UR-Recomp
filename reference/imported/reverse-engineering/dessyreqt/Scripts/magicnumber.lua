

local tinytops = 2 -- If 1, assume tinytops in magic number calculations.  If 0, assumes straight 640 run to finish.  If 2, show both

local textX = 227
local textY = 32

local curBoost = 0
local curX = 0
local B = 0
local D = 0
local magicNumber = 0
local progress = 0
local finishX = 0
local startX = 0
local curTrack = 0
local curLap = 0
local totalLap = 0

while 1 == 1 do

    curTrack = memory.readbyte(0x7E00CE)
    curBoost = memory.readword(0x7E11CD)
    curLap = memory.readbyte(0x7E0EF1)
    curX = memory.readword(0x7E0411)
    
    if curTrack == 0 then --Dragster
        startX = 1088; finishX = 25278; totalLap = 0
    elseif curTrack == 1 then --Zoom Zoo
    	startX = 8961; finishX = 8881
    elseif curTrack == 2 then --Bowl
    	startX = 5776; finishX = 5776
    elseif curTrack == 3 then --Switcher
    	startX = 1584; finishX = 63062
    elseif curTrack == 4 then --Monster
    	startX = 4640; finishX = 4719
    elseif curTrack == 10 then --Looper
    	startX = 1776; finishX = 2439
    elseif curTrack == 11 then --Megajump
    	startX = 9488; finishX = 9704
    elseif curTrack == 12 then --Jumps
    	startX = 0; finishX = 0
    elseif curTrack == 13 then --Flat Fun
    	startX = 2192; finishX = 5206
    elseif curTrack == 14 then --Infinity
    	startX = 720; finishX = 721
    elseif curTrack == 20 then --Dragrace
    	startX = 3264; finishX = 30547
    elseif curTrack == 21 then --Pingpong
    	startX = 7920; finishX = 8150
    elseif curTrack == 22 then --Hill Climb
    	startX = 0; finishX = 0
    elseif curTrack == 23 then --Hybrid
    	startX = 112; finishX = 300
    elseif curTrack == 24 then --Short Cut
    	startX = 7936; finishX = 7710
    elseif curTrack == 30 then --Wario Paint
    	startX = 1408; finishX = 47100
    elseif curTrack == 31 then --Crock
    	startX = 8896; finishX = 9120
    elseif curTrack == 32 then --Downer
    	startX = 464; finishX = 464
    elseif curTrack == 33 then --East
    	startX = 3088; finishX = 58090
    elseif curTrack == 34 then --Hairpin Hill
    	startX = 7968; finishX = 7813
    elseif curTrack == 5 then --Wobble
    	startX = 2272; finishX = 2678
    elseif curTrack == 6 then --Twinpeak
    	startX = 7120; finishX = 7210
    elseif curTrack == 7 then --Skier
    	startX = 128; finishX = 128
    elseif curTrack == 8 then --Loopback
    	startX = 576; finishX = 1590
    elseif curTrack == 9 then --Small Cut
    	startX = 7696; finishX = 7920
    elseif curTrack == 15 then --Last One
    	startX = 16208; finishX = 15660
    elseif curTrack == 16 then --Marathon
    	startX = 4992; finishX = 5189
    elseif curTrack == 17 then --Circle
    	startX = 2464; finishX = 2464
    elseif curTrack == 18 then --Plinkey
    	startX = 32; finishX = 229
    elseif curTrack == 19 then --Jumpover
    	startX = 816; finishX = 1000
    elseif curTrack == 25 then --Down+Up
    	startX = 672; finishX = 1325
    elseif curTrack == 26 then --Highroad
    	startX = 1264; finishX = 1400
    elseif curTrack == 27 then --Spine
    	startX = 2048; finishX = 2048
    elseif curTrack == 28 then --Boo!
    	startX = 160; finishX = 5278
    elseif curTrack == 29 then --Fire Escape
    	startX = 1760; finishX = 1900
    elseif curTrack == 35 then --Vertical
    	startX = 576; finishX = 3860
    elseif curTrack == 36 then --Flash
    	startX = 5440; finishX = 5200
    elseif curTrack == 37 then --Little Dipper
    	startX = 480; finishX = 480
    elseif curTrack == 38 then --Fruitbat
    	startX = 352; finishX = 3900
    elseif curTrack == 39 then --123 Jump
    	startX = 2304; finishX = 2470
    elseif curTrack == 40 then --Griller
    	startX = 2160; finishX = 4550
    elseif curTrack == 41 then --Two Loops
    	startX = 1552; finishX = 1730
    elseif curTrack == 42 then --Neon
    	startX = 5696; finishX = 5696
    elseif curTrack == 43 then --Hamster
    	startX = 384; finishX = 1005
    elseif curTrack == 44 then --To And Fro
    	startX = 3168; finishX = 3540
    end

    B = curBoost
    D = math.abs(finishX - curX)

    if tinytops == 1 or tinytops == 2 then
        magicNumber = D * 328 / 460.5714
        progress = B / magicNumber
    
        --if false then-- startX == finishX then
        --elseif curLap == 1 then
            gui.text(textX,textY, math.floor(progress * 100) .. "%")
    
            if B >= magicNumber then
                gui.text(textX+1, textY+7, "GO!!")
            elseif B + 500 >= magicNumber then
                gui.text(textX+2, textY+7, "-.5")
            elseif B + 1000 >= magicNumber then
                gui.text(textX-1, textY+7, "-1")
            elseif B + 2000 >= magicNumber then
                gui.text(textX-3, textY+7, "-2")            
            end
        --end
    end
        
    if tinytops == 0 or tinytops == 2 then
        magicNumber = D * 1 / 1
        progress = B / magicNumber
    
        --if false then --startX == finishX then
        --elseif curLap == 1 then
            gui.text(textX,textY-21, math.floor(progress * 100) .. "%")    
            if B - 100 >= magicNumber then
                gui.text(textX+1, textY-7-21, "GO!!")
            elseif B + 200 >= magicNumber then
                gui.text(textX+2, textY-7-21, "Soon")
            elseif B + 1000 >= magicNumber then
                gui.text(textX+2, textY-7-21, "-1")
            elseif B + 2000 >= magicNumber then
                gui.text(textX+2, textY-7-21, "-2")                
            end
        --end
    end

    emu.pause()
end

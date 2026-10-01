RAM = {
        cameraYPos = 0x7e041D,
        cameraXPos = 0x7e0419,
        uniXPos = 0x7e0411,
        uniYPos = 0x7e0415,
        trackXSize = 0x7e0d49,
        timer1 = 0x7e0e31,
        timer2 = 0x7e0e33,
        timer3 = 0x7e0e1b,
        backColor = 0x7e0b7e
}

newXValue = 0
newYValue = 0
pressStart = true

function stopTime()
    memory.writebyte(RAM.timer1, 5)
    memory.writebyte(RAM.timer2, 5)
    memory.writebyte(RAM.timer3, 5)
end

function checkPos()
    if math.abs(memory.readword(RAM.cameraXPos) - newXValue) < 40 then
        newXValue = newXValue + 100
        if newXValue > memory.readword(RAM.trackXSize) then
            newXValue = 0
            newYValue = newYValue + 100
        end
    end
end

function setUniPos()    
    memory.writeword(RAM.uniXPos, newXValue+110)
    memory.writeword(RAM.uniYPos, newYValue+110)
end

function nextFrame()
	buttonTable = {start=nil, select=nil, up=nil, down=nil, left=nil, right=nil, A=nil, B=nil, X=nil, Y=nil, L=nil, R=nil}
    if pressStart then
        buttonTable.start = true
    end
    pressStart = not(pressStart)
    joypad.set(1, buttonTable)
    snes9x.frameadvance()
end

while true do
    memory.writebyte(RAM.backColor, 2)
    stopTime()
    checkPos()
    setUniPos()
    nextFrame()
end


-- Settings
local maxY = 14863
local xInc = 100
local yInc = 100

-- Main script
require "gd"

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
snes9xImage = nil;
hugeImage = gd.create(memory.readword(RAM.trackXSize), maxY);
function stopTime()
    memory.writebyte(RAM.timer1, 5)
    memory.writebyte(RAM.timer2, 5)
    memory.writebyte(RAM.timer3, 5)
end
function checkPos()
    if math.abs(memory.readword(RAM.cameraXPos) - newXValue) < 40 and math.abs(memory.readword(RAM.cameraYPos) - newYValue) < 20 then
        newXValue = newXValue + xInc
        if newXValue > memory.readword(RAM.trackXSize) then
            newXValue = 0
            newYValue = newYValue + yInc
        end
		-- like... here?
		snes9xImage = gd.createFromGdStr(gui.gdscreenshot());
		gd.copy(hugeImage, snes9xImage, memory.readword(RAM.cameraXPos), memory.readword(RAM.cameraYPos), 0, 0, snes9xImage:sizeX(), snes9xImage:sizeY());
        hugeImage:png("map.png");
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
while newYValue <= maxY do
    --snes9x.speedmode("nothrottle")
    memory.writebyte(RAM.backColor, 2)
    stopTime()
    checkPos()
    setUniPos()
    nextFrame()
end

hugeImage:png("map.png");

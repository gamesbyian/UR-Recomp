--[[
Uniracers Speed Control Manager (SCUM)

Controls the Uniracer's speed to match, on average, the camera speed. It does 
this by braking if the Uni is ahead of the target camera position and moving
forward if behind it. This results in a rather shaky motion, but it's still
fast so long as the camera speed remains constant.
--]]

minFramesToRun = 0 --will run this many frames and then check for stop conditions
airTolerance = 3 --max airFlag counter, default value = 3
flatTolerance = 30 --max frames on flat, default value = 3

RAM = {
    words = {
        yPos = 0x7E0415,
        xSpeed = 0x7E04B7
    },
    
    bytes = {
        xPosScreen = 0x7E1509,
        airFlag = 0x7E0545,
        cameraXSpeed = 0x7E04F5
    }
}
continue = true

framesRun = 0
flatFrames = 0
lastYPos = 0

continueStatus = ""
controlStatus = ""

maxRightXPos = 50 --found experimentally
maxLeftXPos = 140 --found experimentally
maxCameraSpeed = 16
cameraSpeedUnitSize = 32


function ShouldContinue()
    if framesRun < minFramesToRun then
        return true, "Running"
    end

    local curYPos = memory.readword(RAM.words.yPos)
    
    if (curYPos == lastYPos) then
        flatFrames = flatFrames + 1
    else
        flatFrames = 0
    end
    
    lastYPos = curYPos
    
    if flatFrames > flatTolerance then
        return false, "Stopped execution: Uni is on flat."
    end

    if memory.readbyte(RAM.bytes.airFlag) > airTolerance then
        return false, "Stopped execution: Uni is in air."
    end
    
    local cameraXSpeed = memory.readbyte(RAM.bytes.cameraXSpeed)
    cameraXSpeed = (cameraXSpeed > 127) and cameraXSpeed - 256 or cameraXSpeed
    
    if not (math.abs(cameraXSpeed) == maxCameraSpeed) then
        return false, "Stopped execution: Camera slowed."
    end
    
    return true, "Running"
end

function SetControls(braking, xSpeed)
    local buttonTable = {start=nil, select=nil, up=nil, down=nil, left=nil, right=nil, A=nil, B=nil, X=nil, Y=nil, L=nil, R=nil}

	if braking then
		buttonTable.Y = true
	end
	
	if xSpeed > 0 then
		buttonTable.right = true
	else
		buttonTable.left = true
	end
	
	joypad.set(1, buttonTable)
	framesRun = framesRun + 1
	snes9x.frameadvance()
    
    return "Setting controls. X Speed: " .. xSpeed .. "; Braking: " .. (braking and "true" or "false")
end

function SetStatus()
    gui.text(0, 60, controlStatus)
    
    snes9x.message(continueStatus)
end

function ShouldBrake(xSpeed)
    local tooSlow = math.abs(xSpeed) < ((maxCameraSpeed - 1) * cameraSpeedUnitSize)
    local tooFarAhead = false
    
    local xPosScreen = memory.readbyte(RAM.bytes.xPosScreen)
       
    if xPosScreen < maxLeftXPos and xSpeed < 0 then
        tooFarAhead = true
    end
    
    if xPosScreen > maxRightXPos and xSpeed > 0 then
        tooFarAhead = true
    end
    
    if xPosScreen > 200 then 
        tooFarAhead = true
    end
    
    if tooSlow then
        return false
    elseif tooFarAhead then
        return true
    end
    
    return false
end

while continue do
    local xSpeed = memory.readword(RAM.words.xSpeed)
    xSpeed = (xSpeed > 32767) and xSpeed - 65536 or xSpeed

    local braking = ShouldBrake(xSpeed)
	
    controlStatus = SetControls(braking, xSpeed)
    SetStatus()
    continue, continueStatus = ShouldContinue()    
end
SetStatus()

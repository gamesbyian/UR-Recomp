--This is old. Please use SCUM.
--Change these settings to affect how the program works
local framesToRun = 60
local xRightThreshold = 155 --edge of good speed is 175, default value=155
local xLeftThreshold = 55 --edge of good speed is 15, default value=35
local speed = 500
--leave these alone
local curSpeed = 0
local framesRun = 0
local braking = false
local xPos = 0
local governing = false

while framesRun <= framesToRun do
	curSpeed = memory.readword(0x7E04B7)
	xPos = memory.readbyte(0x7E1509)
	if curSpeed > 32768 then -- Until 0.04 of snes9x-lua adds signed version of readword
		curSpeed = curSpeed - 65536
	end
	gui.text(0, 40, "Speed : " .. curSpeed)
	
	if xPos >= xRightThreshold or xPos <= xLeftThreshold then
		governing = true
	end
	
	if xPos < xRightThreshold and xPos > xLeftThreshold then
		governing = false
        braking = false
	end
	
	if governing then
		if math.abs(curSpeed) >= speed then
			braking = true
		end
		
		if math.abs(curSpeed) <= speed then
			braking = false
		end
	end
	
	if braking then
		gui.text(0, 50, "Braking : true")
	else
		gui.text(0, 50, "Braking : false")
	end
	
	buttonTable = {start=nil, select=nil, up=nil, down=nil, left=nil, right=nil, A=nil, B=nil, X=nil, Y=nil, L=nil, R=nil}

	if braking then
		buttonTable.Y = true
	end
	
	if curSpeed > 0 then
		buttonTable.right = true
	else
		buttonTable.left = true
	end
	
	joypad.set(1, buttonTable)
	framesRun = framesRun + 1
    gui.text(0, 60, "Frames Run:" .. framesRun)
	snes9x.frameadvance()
end

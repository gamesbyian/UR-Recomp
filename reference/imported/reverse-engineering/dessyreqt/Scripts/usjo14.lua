
--==========================================================================
--  _   _   __   _   _   _____        ___   _____   _____   _____    _____  
-- | | | | |  \ | | | | |  _  \      /   | /  ___| | ____| |  _  \  /  ___/ 
-- | | | | |   \| | | | | |_| |     / /| | | |     | |__   | |_| |  | |___  
-- | | | | | |\   | | | |  _  /    / / | | | |     |  __|  |  _  /  \___  \ 
-- | |_| | | | \  | | | | | \ \   / /  | | | |___  | |___  | | \ \   ___| | 
-- \_____/ |_|  \_| |_| |_|  \_\ /_/   |_| \_____| |_____| |_|  \_\ /_____/ 
-- 
--        |¯  ¯|¯ | | |\| ¯|¯   /¯\ |\| |¯\    ¯|¯ | | |\/| |¯| 
--         ¯|  |  |_| | |  |    |¯| | | |_/   |_|  |_| |  | |¯                                                      
--  _____  ¯_____   _____   _       ___  ___   _   ______  _____   _____   
-- /  _  \ |  _  \ |_   _| | |     /   |/   | | | |___  / | ____| |  _  \  
-- | | | | | |_| |   | |   | |    / /|   /| | | |    / /  | |__   | |_| |  
-- | | | | |  ___/   | |   | |   / / |__/ | | | |   / /   |  __|  |  _  /  
-- | |_| | | |       | |   | |  / /       | | | |  / /__  | |___  | | \ \  
-- \_____/ |_|       |_|   |_| /_/        |_| |_| /_____| |_____| |_|  \_\ 
--
--==========================================================================
--                           February 14th, 2008
--                           (Internal Version 14)
--==========================================================================

--- IMPORTANT REMINDER: LUA SCRIPTING BREAKS WITH SNES9X SLOWDOWN (50% or 2% in "normal" speed mode for example)
--- WARNING: THIS SCRIPT OVERWRITES SAVESTATE SLOT 11.
--[[
commented stuff

--]]
function main()
	-- ====== Usage notes =======
	-- In general, to find the true optimum you'll want every permutation of the following:
	-- 0.) Always back up a few frames and use a nice wide framewait window (like 0 to 5 or 0 to 10) even if you think you know the best jump frame
	-- 1.) reversefliproll = 1; reversefliproll = 0
	-- 2.) twistoffset = 1; twistoffset = -3; twistoffset = -5; (if you have some framewait, try a twistoffset equal to your maxframewait?)
	-- 3.) If its a short jump (less than a TtFT), or you're using minimumy or maximumy, try assumenothing = 1, but try permutations with assumenothing = 0 as well!
	-- 4.) If you think maxBframes is a good idea, try the above permutations with maxBframes = 0 too
	-- For extra diligence, watch the bot run in frame advance (or even just trick executer on a trick it isn't finding), and see if you need some flip or roll overcorrect

	-- ====== Parameters for Script ======
	local startframe = 0 -- The lowest value to use for framewait
	local maxframewait = 0 -- The highest value to use for framewait (can be set equal to startframe)
	local frameincrement = 1 -- The increment by which it steps through the framewait range

	local changedirection = 0 -- 1 = yes, 0 = no -- To be used if you want to score the speed of a jump based on going the opposite direction as the jump started (zippers)
	local forcedirection = 0 -- 1 = right, -1 = left -- To be used if you have zero speed or another case where you want the bot to go in a direction

	local reversefliproll = 1 -- 0 = no, 1 = yes -- Change the order in which you flip and roll, always try a jump both with and without this!  On a good ramp, particularly steep ones, you will likely want this to = 1

	local flipovercorrect = 0 -- Extra frames of flipping after all flipping and rolling are complete
	local rollovercorrect = 0 -- Ditto, try them both, sometimes flipping and rolling get mixed up due to z rotation
	local zflippreference = 0 -- 0 = perform a flip, 1 = perform a roll (default) -- What button do you hold with the z-flip if not flipping or rolling

	local maxBframes = 0 -- default = 0; only works with framewait = 0 (startframe = 0 and maxframewait = 0) -- hold B for this number of frames and no more
	local twistoffset = -3 -- How many frames back to try starting a pre-twist.  Set to -3 to stop pre-twisting?

	local assumenothing = 0 -- 0 = no, 1 = yes, if yes, will start each jump trying no tricks and build up from there, vs. the "conservative guess".  useful if trying to find a case without a TtT
	local maximumy =  3200000 -- Y to end above, use if trying to get up on a platform, should be tried with assumenothing = 1
	local minimumy = -3200000 -- Y to end below, use if trying to get down to a level, must be used with assumenothing = 1
	local wholetwistsonly = 1 -- 0 = no, 1 = yes, increments twist attempts by 2 instead of 1

	local searchwindow = 1 -- How many frames after landing to wait until assessing speed and boost
	local minjump = 4 -- Minimum jump duration worth looking at in more detail, change if some framewaits hit an immediate obstacle and you're worried about compute time
	local maxtabletopextrawait = 15 -- How many frames of delay to search to make a tabletop work, if it doesn't find a good one, it will erroneously assume tabletops are finishing
	local maxtwistwait = 20 -- How many frames of delay to search to make the first twist work, if it doesn't find one, it will skip that framewait, default = 20

	local ruttolerance = 15 -- For getting out of local minima in the global search, set to higher number if you're in no hurry, but unlikely to find anything new past 15
	local infiniteloopdetection = 300 -- Maximum duration of framewait + jump time before realizing its stuck in an in-game infinite loop and trying the next framewait

	--- IMPORTANT REMINDER: LUA SCRIPTING BREAKS WITH SNES9X SLOWDOWN (50% or 2% in "normal" speed mode)
	snes9x.speedmode("nothrottle")
	--snes9x.speedmode("maximum")

	-- =========== Trick Execution Mode Controls ===============
	local trickexecution = 0 -- 0 = off, 1 = on; if
	local Tt = 1
	local F = 3
	local R = 0
	local T = 4
	local Z = 1
	-- Note: if you have a Tt and Z without a T, it will fail at the Z. (until someone comes up with the generalized timing rules for that case (screw Zflips!))

	-- ============== Trick Execution Usage Notes ==============
	-- When you run the optimizer, note the "Tried: " trick on the final paused output frame!  Note half-twists too!
	-- This is the input required to recreate the result seen on the "Made: " line
	-- Just because the ROM told you it landed a certain trick doesn't mean inputting the landed trick into the trick executer will cause it to repeat

	if trickexecution == 1 then
		maxframewait = startframe
		frameincrement = 1    
		--changedirection has no effect due to not scoring/optimizing
		--searchwindow has no effect due to not scoring/optimizing
		--assumenothing has no effect due to specifying the trick
		--maximumy has no effect due to not scoring/optimizing
		--minimumy has no effect due to not scoring/optimizing
		--wholetwistsonly has no effect due to specifying the trick
		T = T * 2 -- Convert to half-twists    
	end

	-- =============== Output notes =====================
	--- On the final paused frame, the bot will tell you the parameters it learned so that you can recreate the trick easily yourself
	-- twistwait is how many frames after B is pressed to press reverse direction (may be impacted by twistoffset)
	-- twistregisters is how many frames from the start until the twist will register (for tabletop pre-knowledge)
	-- tabletopextrawait is how many frames after twistregisters to delay until pressing X
	-- zwait is how many frames after the tabletop and twist finish before pressing and holding X
	-- zwait2 is how many frames to wait after a previous zflip has finished before pressing and holding X again (after the one frame not pressing X)
	-- finalflipframe is the frame the last flip will end on, allowing for pre-knowledge for rollwait
	-- rollwait = 1 means stopping your first rotating stunt (flip or roll) one frame before it registers and pressing the opposite direction (L/R)

	local twistduration = 9 -- Not used, I think
	local tabletopwait = 8 -- Not used, I think
	local tabletopair = 9 -- Airflag required for tabletops
	local tabletoptime = 7 -- I think this is used... duration of front half of tabletop?
	local tabletopspeed = 600 -- Not used
	local maxtwists = 999 -- Not used, I'm pretty sure...

	local mode = 1 -- 0 = initializing, 1 = jumping, 2 = first twist timing, 3 = tabletop timing, 4 = stunt optimization, zflip timing, rollwait timing, replaying, 5 = done
	if trickexecution == 1 then
		mode = 2
	end
	local jumpstatus = 0 -- 0 = not trying to jump, 1 = trying to jump, 2 = airborne, 3 = peaked, 4 = landed
	local twiststatus = 0 -- 0 = not trying, 1 = waiting for back twist to finish, 2 = waiting for front twist to finish
	local tabletopstatus = 0
	local zflipstatus = 0
	local rollstatus = 0
	local flipstatus = 0
	local reload = 0
	local strategy = 1 -- 1 = build up, 2 = individual maximums, 3 = tear down from maxes

	local yspeed = 0
	local airflag = 0
	local curframe = 0
	local afterframe = 0 -- Counter for frames after jump
	local thisjumpduration = 0
	local bestjumpduration = 0
	local jumpiestframe = 0
	local twistwait = 0
	local numtwists = 0
	local numtabletops = 0
	local numzflips = 0
	local numrolls = 0
	local numflips = 0
	local thismaxtwists = 0
	local thismaxtabletops = 0
	local thismaxzflips = 0
	local thismaxrolls = 0
	local thismaxflips = 0
	local tabletopcounter = 0
	local finalscore = 0
	local bestfinalscore = -9999
	local lastscore = 0
	local lastaddition = 0
	local consecutivefailures = 0
	local strategytext = ""
	local lastboost = 0
	local lastspeed = 0
	local twistregisters = 0
	local tabletopextrawait = 0
	local zflipframe = 0
	local twistcounter = 0
	local zflipinplay = 0
	local rutcounter = 0
	local zrotation = 0
	local zprerotation = 0
	local zwait = 0
	local zwaited = 0
	local zwait2 = 0
	local zfromthegrave = 0
	local backwardspaddles = 0
	local realboostmeter = 0
	local thisrollovercorrect = 0
	local thisflipovercorrect = 0
	local lastframetwist = 0
	local lastframetabletop = 0
	local finalflipframe = 0
	local rollwait = 0
	local ycoordinate = 0

	local bestscoringtwists = 0
	local bestscoringtabletops = 0
	local bestscoringzflips = 0
	local bestscoringrolls = 0
	local bestscoringflips = 0
	local bestscoringtwistwait = 0
	local bestscoringframewait = 0
	local bestscoringtabletopextrawait = 0
	local bestscoringzwait = 0
	local bestscoringzwait2 = 0
	local bestscoringtwistregisters = 0
	local bestscoringrollwait = 0
	local bestscoringfinalflipframe = finalflipframe

	local maxtwistonly = 0
	local maxtabletopsonly = 0
	local maxzflipsonly = 0
	local maxrollsonly = 0
	local maxflipsonly = 0

	local completedtwists = 0
	local completedtabletops = 0
	local completedzflips = 0
	local completedrolls = 0
	local completedflips = 0

	local jumping = 0
	local reverse = 0
	local rolling = 0  -- rolls go in the direction (front flip)
	local flipping = 0 -- flips go against direction (back flip)
	local xing = 0

	-- ====== Setup our task ===========
	-- Create a saveslot to use
	local startSS = savestate.create(11) -- Chose 11 for the hell of it, snes9x seems to eventually crash if you use lua-only SS
	savestate.save(startSS) 

	local framewait = startframe

	-- Figure out which direction we're going
	local curspeed = memory.readword(0x7E04B7) -- Alternatively, 0x7E0F9F
	local horzdirection = 1 -- 1 = right, -1 = left
	if curspeed > 32768 then -- Until 0.04 of snes9x-lua adds signed version of readword
		curspeed =  curspeed - 65536
		horzdirection = -1
	end

	if forcedirection == 1 then
		horzdirection = 1
	elseif forcedirection == -1 then
		horzdirection = -1
	end

	if changedirection == 1 then
		changedirection = -1
	else
		changedirection = 1
	end

	-- ========== Main loop =============

	while mode < 5 do      
		
		jumping = 0
		reverse = 0
		rolling = 0
		flipping = 0
		xing = 0

		if reload == 1 then
			savestate.load(startSS)        
			gui.text(0, 130, "Reloaded Savestate this frame!")
			jumpstatus = 0     
			twiststatus = 0
			tabletopstatus = 0
			zflipstatus = 0
			rollstatus = 0
			flipstatus = 0
			tabletopcounter = 0
			twistcounter = 0
			zflipframe = 0
			zflipinplay = 0
			zwaited = 0
			zfromthegrave = 0
			backwardspaddles = 0
			completedtwists = 0
			completedtabletops = 0
			completedzflips = 0
			completedrolls = 0
			completedflips = 0
			finalscore = 0
			thisrollovercorrect = rollovercorrect
			thisflipovercorrect = flipovercorrect        
			if mode == 1 then
				thisjumpduration = 0
			end
			afterframe = 0
			curframe = 0
			reload = 0
		end
		
		curspeed = memory.readword(0x7E04B7)
		if curspeed > 32768 then -- Until 0.04 of snes9x-lua adds signed version of readword
			curspeed =  curspeed - 65536
		end
		yspeed = memory.readword(0x7E04BB)
		if yspeed > 32768 then
			yspeed = yspeed - 65536
			vertdirection = 1 -- Going up
		else
			vertdirection = -1 -- Going down
		end
		
		airflag = memory.readbyte(0x7E0545)
		numtwists = memory.readbyte(0x7E0F61)
		numtabletops = memory.readbyte(0x7E042F)
		numzflips = memory.readbyte(0x7E042B)
		numrolls = memory.readbyte(0x7E11F9)
		numflips = memory.readbyte(0x7E11FD)
		zrotation = memory.readbyte(0x7E0DFD)
		zprerotation = memory.readbyte(0x7E0F57)
		realboostmeter = memory.readword(0x7E11CD)
		ycoordinate = memory.readword(0x7E0415)
		
		if reversefliproll == 1 then
			local temp = numrolls
			numrolls = numflips
			numflips = temp
		end
		
		gui.text(0, 150, "Xv: " .. curspeed .. "(" .. horzdirection .. ") Yv: " .. yspeed .. "(" .. vertdirection .. ")")
		gui.text(0, 160, "Air:" .. airflag .. " Tw:" .. numtwists .. " Tt:" .. numtabletops .. " Zf:" .. numzflips .. " Ro:" .. numrolls .. " Fl:" .. numflips)
		
		if mode == 1 then
			gui.text(0,0, "Framewait: " .. framewait .. ", measuring jump.")
			if jumpstatus == 0 then
				gui.text(0, 10, "Not trying to jump just yet.")
				if curframe >= framewait then
					jumpstatus = 1
					jumping = 1
				else
					jumping = 0
				end
			elseif jumpstatus == 1 then
				gui.text(0, 10, "Trying to jump!")
				jumping = 1
				if airflag >= 2 then
					jumpstatus = 2
					thisjumpduration = 2
				end
			elseif jumpstatus == 2 then
				gui.text(0, 10, "Airborne for " .. thisjumpduration .. ".")
				thisjumpduration = thisjumpduration + 1
				jumping = 1
				if vertdirection == -1 then
					jumpstatus = 3
				end
				if airflag == 0 then
					jumpstatus = 4
				end
			elseif jumpstatus == 3 then
				gui.text(0, 10, "Peaked, airborne for " .. thisjumpduration .. ".")
				thisjumpduration = thisjumpduration + 1
				jumping = 0
				if airflag == 0 then
					jumpstatus = 4
				end        
			elseif jumpstatus == 4 then
				gui.text(0, 10, "Landed after " .. thisjumpduration .. ".")
				jumping = 0
				if thisjumpduration > bestjumpduration then
					bestjumpduration = thisjumpduration
					jumpiestframe = framewait
				end
				if thisjumpduration < minjump then
					if framewait >= maxframewait then
						mode = 4
						strategy = 4
						thismaxtwists = bestscoringtwists
						thismaxtabletops = bestscoringtabletops
						thismaxzflips = bestscoringzflips
						thismaxrolls = bestscoringrolls
						thismaxflips = bestscoringflips
						twistwait = bestscoringtwistwait
						framewait = bestscoringframewait
						tabletopextrawait = bestscoringtabletopextrawait
						zwait = bestscoringzwait
						zwait2 = bestscoringzwait2
						twistregisters = bestscoringtwistregisters
						rollwait = bestscoringrollwait
						finalflipframe = bestscoringfinalflipframe
						lastscore = 0
						lastaddition = 0
						consecutivefailures = 0
						rutcounter = 0                                   
						snes9x.speedmode("normal")                            
					else
						framewait = framewait + frameincrement
						reload = 1
						mode = 1                
					end
				else
					reload = 1
					mode = 2                
					twistwait = 0
				end
			end
			
		elseif mode == 2 then
			gui.text(0,0, "Framewait: " .. framewait .. ", find twist frame.")        
			gui.text(0,140, "Jump duration: " .. thisjumpduration .. ".")
			if jumpstatus == 0 then
				if curframe >= framewait then
					jumpstatus = 1
					jumping = 1
				else
					jumping = 0
				end
			elseif jumpstatus == 1 then
				jumping = 1
				if airflag >= 2 then
					jumpstatus = 2
				end
			elseif jumpstatus == 2 then
				jumping = 1
				if vertdirection == -1 then
					jumpstatus = 3
				end
				if airflag == 0 then
					jumpstatus = 4
				end
			elseif jumpstatus == 3 then
				jumping = 0
				if airflag == 0 then
					jumpstatus = 4
				end        
			elseif jumpstatus == 4 then
				jumping = 0
			end        

			if twiststatus == 0 then
				gui.text(0, 10, "Twistwait: " .. twistwait .. ", waiting reverse.")
				if curframe >= (twistwait + framewait - twistoffset) then
					gui.text(0, 20, "On frame " .. curframe .. " I tried to twist.")
					twiststatus = 1
					reverse = 1
				else
					reverse = 0
				end
			elseif twiststatus == 1 then
				gui.text(0, 10, "Twistwait: " .. twistwait .. ", wait on register.")
				reverse = 0
				if numtwists > lastframetwist then
					twistregisters = curframe
					twiststatus = 2
					reload = 1
					mode = 3
					tabletopextrawait = 0
					thismaxtwists = 2
					thismaxtabletops = 1
					thismaxzflips = 0
					thismaxrolls = 0
					thismaxflips = 0
					if trickexecution == 1 and Tt == 0 then
						thismaxtabletops = 0
					end
				end
			end
			
			if (trickexecution == 1 and T == 0) then
				twistregisters = curframe                
				reload = 1
				mode = 3
				tabletopextrawait = 0                
				thismaxtwists = 0
				thismaxtabletops = 1
				thismaxzflips = 0
				thismaxrolls = 0
				thismaxflips = 0    
				if trickexecution == 1 and Tt == 0 then
					thismaxtabletops = 0
				end
			end
			
			if (twiststatus == 1 and (curframe - framewait > 20 or jumpstatus == 4)) then
				twistwait = twistwait + 1
				if twistwait > maxtwistwait then                
					if framewait >= maxframewait then
						mode = 4
						strategy = 4
						thismaxtwists = bestscoringtwists
						thismaxtabletops = bestscoringtabletops
						thismaxzflips = bestscoringzflips
						thismaxrolls = bestscoringrolls
						thismaxflips = bestscoringflips
						twistwait = bestscoringtwistwait
						framewait = bestscoringframewait
						tabletopextrawait = bestscoringtabletopextrawait
						zwait = bestscoringzwait
						zwait2 = bestscoringzwait2
						twistregisters = bestscoringtwistregisters
						rollwait = bestscoringrollwait
						finalflipframe = bestscoringfinalflipframe
						lastscore = 0
						lastaddition = 0
						consecutivefailures = 0
						rutcounter = 0                                   
						snes9x.speedmode("normal")                            
					else
						framewait = framewait + frameincrement
						reload = 1
						mode = 1                
					end
				else
					reload = 1
					mode = 2
				end
			end
		elseif mode == 3 then
			gui.text(0,0, "Framewait: " .. framewait .. ", Tabletop timing.")
			gui.text(0,10, "Tabletop extra wait: " .. tabletopextrawait)
			if jumpstatus == 0 then            
				if curframe >= framewait then
					jumpstatus = 1
					jumping = 1                
				else
					jumping = 0
				end
			elseif jumpstatus == 1 then            
				jumping = 1
				if airflag >= 2 then
					jumpstatus = 2
				end
			elseif jumpstatus == 2 then            
				jumping = 1
				if vertdirection == -1 then
					jumpstatus = 3
				end
				if airflag == 0 then
					jumpstatus = 4
				end
			elseif jumpstatus == 3 then            
				jumping = 0
				if airflag == 0 then
					jumpstatus = 4
				end        
			elseif jumpstatus == 4 then            
				jumping = 0
				afterframe = afterframe + 1
			end
			
			if twiststatus == 0 then
				if curframe >= (twistwait + framewait - twistoffset) then
					if (jumpstatus == 4 or completedtwists >= thismaxtwists) then
						gui.text(0, 50, "Tw: At Max. All done.")
						twiststatus = 0
						reverse = 0
					else
						gui.text(0, 50, "Tw: Reversing!")
						twiststatus = 1
						reverse = 1
					end
				else
					gui.text(0, 50, "Tw: Waiting to Reverse")
					reverse = 0                
				end
			elseif twiststatus == 1 then
				reverse = 0
				if numtwists > completedtwists then
					completedtwists = numtwists
					twiststatus = 2
					gui.text(0, 50, "Tw: Finished backwards leg")
				else
					gui.text(0, 50, "Tw: Waiting on Backwards")
				end
			elseif twiststatus == 2 then
				if numtwists > completedtwists then
					completedtwists = numtwists
					if completedtwists >= thismaxtwists then
						gui.text(0, 50, "Tw: Finished last twist")
						reverse = 0
						twiststatus = 0
					else
						gui.text(0, 50, "Tw: Starting another twist")
						reverse = 1
						twiststatus = 1
					end
				else
					gui.text(0, 50, "Tw: Waiting on Forward")
					reverse = 0
				end                
			end
			
			gui.text(0, 20, curframe .. " " .. twistregisters .. " " .. tabletopextrawait .. " " .. thismaxtwists)
			if tabletopstatus == 0 then
				if airflag == tabletopair then
					if (jumpstatus == 4 or completedtabletops >= thismaxtabletops) then
						tabletopstatus = 0
						xing = 0
						gui.text(0, 60, "Tt: All done.")
					elseif (curframe < twistregisters + tabletopextrawait - 1 and thismaxtwists > 0) then
						tabletopstatus = 0
						xing = 0
						gui.text(0, 60, "Tt: Waiting for twist")
					else
						tabletopstatus = 1
						tabletopcounter = 0
						xing = 1
						gui.text(0, 60, "Tt: Starting first half")
					end
				elseif (airflag == tabletopair-1 and (numtwists >= 1 or (tabletopextrawait == 0 and thismaxtwists == 0))) then
					tabletopstatus = 1
					tabletopcounter = 0
					xing = 1
					gui.text(0, 60, "Tt: Starting first half")
				else
					gui.text(0, 60, "Tt: Waiting")
					xing = 0
				end
			elseif tabletopstatus == 1 then
				xing = 0
				tabletopcounter = tabletopcounter + 1
				if numtabletops > lastframetabletop then            
					if trickexecution == 1 then
						reload = 1
						mode = 4
						strategy = 1
						thismaxtwists = T
						thismaxtabletops = Tt
						thismaxzflips = Z
						thismaxflips = F
						thismaxrolls = R
						strategytext = "First try at specified trick"
						lastscore = 0
						lastaddition = 0
						consecutivefailures = 0
						rutcounter = 0           
						zwait = 0
						zwait2 = 0
						rollwait = 0
						finalflipframe = 0
					else
						gui.text(0, 60, "Tt: Tabletop worked w/ " .. tabletopextrawait .. " wait")
						reload = 1
						mode = 4
						strategy = 1
						thismaxtwists = math.max(0, math.floor((thisjumpduration - 40) / 12))
						if wholetwistsonly == 1 and thismaxtwists % 2 == 1 then
							thismaxtwists = math.max(0, thismaxtwists - 1)
						end
						thismaxtabletops = math.max(0, math.min(1, thisjumpduration - (9 + 8 + 8 + 1)))
						thismaxzflips = math.max(0, math.floor((thisjumpduration - (9 + 8 + 8 + 1)) / 50))
						thismaxrolls = math.max(0, math.floor((thisjumpduration - 30) / 30))
						thismaxflips = math.max(0, math.min(1, math.floor(thisjumpduration / 30)))
						if thismaxrolls > 4 then
							thismaxflips = thismaxflips + (thismaxrolls - 4)
							thismaxrolls = 4
						end
						
						strategytext = "Conservative guess"
						if assumenothing == 1 then
							thismaxtwists = 0
							thismaxtabletops = 0
							thismaxzflips = 0
							thismaxrolls = 0
							thismaxflips = 0
							strategytext = "Assume nothing!"
						end
						
						lastscore = 0
						lastaddition = 0
						consecutivefailures = 0
						rutcounter = 0           
						zwait = 0
						zwait2 = 0
						rollwait = 0
						finalflipframe = 0
					end
				elseif tabletopcounter >= tabletoptime + 2 then                
					if tabletopextrawait >= maxtabletopextrawait then
						if framewait >= maxframewait then
							mode = 4
							strategy = 4
							thismaxtwists = bestscoringtwists
							thismaxtabletops = bestscoringtabletops
							thismaxzflips = bestscoringzflips
							thismaxrolls = bestscoringrolls
							thismaxflips = bestscoringflips
							twistwait = bestscoringtwistwait
							framewait = bestscoringframewait
							tabletopextrawait = bestscoringtabletopextrawait
							zwait = bestscoringzwait
							zwait2 = bestscoringzwait2
							twistregisters = bestscoringtwistregisters
							rollwait = bestscoringrollwait
							finalflipframe = bestscoringfinalflipframe
							lastscore = 0
							lastaddition = 0
							consecutivefailures = 0
							rutcounter = 0                                   
							snes9x.speedmode("normal")                            
						else
		
							framewait = framewait + frameincrement
							reload = 1
							mode = 1                    
						end
					else                    
						tabletopextrawait = tabletopextrawait + 1
						tabletopcounter = 0
						reload = 1
						mode = 3
					end
				else
					gui.text(0, 60, "Tt: Frame " .. tabletopcounter .. "/" .. tabletoptime+2 .. " elapsed")
				end                
				
			end
			
			if trickexecution == 1 and Tt == 0 then
				reload = 1
				mode = 4
				strategy = 1
				thismaxtwists = T
				thismaxtabletops = Tt
				thismaxzflips = Z
				thismaxflips = F
				thismaxrolls = R
				strategytext = "First try at specified trick"
				lastscore = 0
				lastaddition = 0
				consecutivefailures = 0
				rutcounter = 0           
				zwait = 0
				zwait2 = 0
				rollwait = 0
				finalflipframe = 0
			end
			if (curframe >= infiniteloopdetection) then
				framewait = framewait + frameincrement
				reload = 1
				mode = 1
			end
			
		elseif mode == 4 then
			gui.text(0,0, "Framewait: " .. framewait .. ", stunt optimization.")
			gui.text(0, 20, "Try Tw:" .. thismaxtwists .. " Tt:" .. thismaxtabletops .. " Zf:" .. thismaxzflips .. " Ro:" .. thismaxrolls .. " Fl:" .. thismaxflips)
			gui.text(0, 30, "Pro Tw:" .. completedtwists .. " Tt:" .. completedtabletops .. " Zf:" .. completedzflips .. " Ro:" .. completedrolls .. " Fl:" .. completedflips)
			gui.text(0, 100, consecutivefailures .. ": " .. strategytext)
			gui.text(0, 110, "LBo: " .. lastboost .. " LSp: " .. lastspeed)
			gui.text(0, 120, "LSc: " .. lastscore .. " BSc: " .. bestfinalscore .. "(" .. rutcounter .. "/" .. ruttolerance .. ")")
			if trickexecution == 1 then
				gui.text(0,10, "--Trick Execution Mode!--")
			elseif strategy == 1 then
				gui.text(0,10, "Trying to build up to best combo.")
			elseif strategy == 2 then
				gui.text(0,10, "Maximizing each stunt individually.")
			elseif strategy == 3 then
				gui.text(0,10, "Tearing down from maximum.")
			elseif strategy == 4 then
				gui.text(0,10, "REPLAYING BEST OPTION!")
			end
		
			if jumpstatus == 0 then
				gui.text(0, 40, "Jump: Waiting")
				if curframe >= framewait then
					jumpstatus = 1
					jumping = 1                
				else
					jumping = 0
				end
			elseif jumpstatus == 1 then
				gui.text(0, 40, "Jump: Trying")
				jumping = 1
				if airflag >= 2 then
					jumpstatus = 2
					completedtwists = 0
					completedtabletops = 0
					completedzflips = 0
					completedrolls = 0
					completedflips = 0
				end
			elseif jumpstatus == 2 then
				gui.text(0, 40, "Jump: Airborne")
				jumping = 1
				if vertdirection == -1 then
					jumpstatus = 3
				end
				if airflag == 0 then
					jumpstatus = 4
				end
			elseif jumpstatus == 3 then
				gui.text(0, 40, "Jump: Peaked")
				jumping = 0
				if airflag == 0 then
					jumpstatus = 4
				end        
			elseif jumpstatus == 4 then
				gui.text(0, 40, "Jump: Landed")
				jumping = 0
				afterframe = afterframe + 1
				twiststatus = 0
				tabletopstatus = 0
				zflipstatus = 0
				flipstatus = 0
				rollstatus = 0
			end
			
			if twiststatus == 0 then
				if curframe >= (twistwait + framewait - twistoffset) then
					if (jumpstatus == 4 or completedtwists >= thismaxtwists) then
						gui.text(0, 50, "Tw: At Max. All done.")
						twiststatus = 0
						reverse = 0
						zflipframe = 1
					elseif tabletopstatus == 1 or tabletopstatus == 2 then
						gui.text(0, 50, "Tw: Waiting on Tt")
						reverse = 0                                             
					elseif zflipinplay > 1 then
						gui.text(0, 50, "Tw: Z-flip in play for " .. zflipinplay - 1)
						twiststatus = 0
						reverse = 0
						zflipframe = 0
					else
						if zfromthegrave > 1 then
							zfromthegrave = zfromthegrave - 1
							twiststatus = 0
							reverse = 0
							zflipframe = 0                        
							gui.text(0, 50, "Tw: Wise Fwom The Gwave! (" .. zfromthegrave .. ")")
						else
							if zfromthegrave == 1 then
								zfromthegrave = 2
							end
							gui.text(0, 50, "Tw: Reversing!")
							twistcounter = 0
							twiststatus = 1
							reverse = 1
							zflipframe = 1
						end
					end
				else
					gui.text(0, 50, "Tw: Waiting to Reverse")
					reverse = 0                
				end
			elseif twiststatus == 1 then
				reverse = 0
				zflipframe = 0
				if (numtwists > completedtwists and jumpstatus > 1) then
					completedtwists = numtwists
					twiststatus = 2
					twistcounter = 0
					gui.text(0, 50, "Tw: Finished backwards leg")                            
				else
					gui.text(0, 50, "Tw: Waiting on Backwards")
				end
			elseif twiststatus == 2 then
				if numtwists > completedtwists then
					completedtwists = numtwists
					zflipframe = 1
					if completedtwists >= thismaxtwists then
						gui.text(0, 50, "Tw: Finished last twist")
						reverse = 0
						twiststatus = 0
					else
						if zfromthegrave > 1 then
							zfromthegrave = zfromthegrave - 1
							twiststatus = 0
							reverse = 0
							zflipframe = 0                        
							gui.text(0, 50, "Tw: Wise Fwom The Gwave! (" .. zfromthegrave .. ")")
						else    
							gui.text(0, 50, "Tw: Starting another twist")
							reverse = 1
							twiststatus = 1
						end
					end
			   else
					zflipframe = 0
					gui.text(0, 50, "Tw: Waiting on Forward")
					reverse = 0
				end
			elseif twiststatus == 3 then
				
					twiststatus = 1
					reverse = 1
			end
			
			if tabletopstatus == 0 then
				if airflag == tabletopair then
					if (jumpstatus == 4 or completedtabletops >= thismaxtabletops) then
						tabletopstatus = 0
						xing = 0
						gui.text(0, 60, "Tt: All done.")
					elseif (curframe < twistregisters + tabletopextrawait - 1 and thismaxtwists > 0) then
						tabletopstatus = 0
						xing = 0
						gui.text(0, 60, "Tt: Waiting for twist")
					else
						tabletopstatus = 1
						tabletopcounter = 0
						xing = 1
						gui.text(0, 60, "Tt: Starting first half")
						if (twiststatus == 1 and tabletopextrawait > 9) or twiststatus == 2 then
							gui.text(0, 170, "Tw: Late Tt, resetting Tw")
							if numtwists == 1 then
								twiststatus = 2
							else
								twiststatus = 0
							end                            
						end 
					end
				elseif (airflag == tabletopair-1 and (numtwists >= 1 or (tabletopextrawait == 0 and thismaxtwists == 0))) then
					tabletopstatus = 1
					tabletopcounter = 0
					xing = 1
					gui.text(0, 60, "Tt: Starting first half")
								  
				else
					gui.text(0, 60, "Tt: Waiting")
					xing = 0
				end
			elseif tabletopstatus == 1 then
				xing = 0
				tabletopcounter = tabletopcounter + 1            
				if tabletopcounter >= tabletoptime + 1 then
					xing = 1
					tabletopstatus = 2
					tabletopcounter = 0
					gui.text(0, 60, "Tt: Starting second half")
				else
					gui.text(0, 60, "Tt: Frame " .. tabletopcounter .. "/" .. tabletoptime .. " elapsed")
				end
			elseif tabletopstatus == 2 then
				xing = 0
				tabletopcounter = tabletopcounter + 1
				if tabletopcounter >= tabletopwait then
					completedtabletops = completedtabletops + 1
					tabletopstatus = 6
					gui.text(0, 60, "Tt: Finished it!")
				else
					gui.text(0, 60, "Tt: Frame " .. tabletopcounter .. "/" .. tabletopwait .. " elapsed")
				end
			elseif tabletopstatus == 6 then
				gui.text(0, 60, "Tt: All done")
			end
			
			gui.text(0, 130, zflipinplay .. " " .. twiststatus .. " " .. zflipframe .. " " .. zrotation .. " " .. zprerotation .. " " .. zfromthegrave)
			if zflipstatus == 0 then            
				if (tabletopstatus == 6 or (jumpstatus > 0 and thismaxtabletops <= 0)) then
					if (jumpstatus == 4 or completedzflips >= thismaxzflips) then
						zflipstatus = 0
						xing = 0
						gui.text(0, 70, "Zf: All done")
					elseif zflipinplay > 1 then
						if zprerotation == 0 then
							zflipstatus = 0
							xing = 0
							gui.text(0, 70, "Zf: Waiting for 2nd z-flip")
						else
							zwait2 = 1
							reload = 1
							gui.text(0, 70, "Zf: SON OF A BITCH!!!!")
						end
					elseif thismaxtwists > 0 and numtwists <= 2 and tabletopextrawait > 9 then
						zflipstatus = 0
						xing = 0
						gui.text(0, 70, "Zf: Waiting on T after late Tt")
					elseif (zflipinplay == 1 or twiststatus == 0 or zflipframe == 1) then
						if (zwait == 1 and zwaited == 0) then
							zflipstatus = 0
							xing = 0
							zflipinplay = 2
							zwaited = 1
							gui.text(0, 70, "Zf: Delaying one frame")
						elseif (zwait == 1 and zwaited > 1) then
							zflipstatus = 0
							xing = 0
							zflipinplay = 2
							zwaited = zwaited - 1
							gui.text(0, 70, "Zf: Delaying one frame")
						else
							xing = 1
							zflipstatus = 1
							gui.text(0, 70, "Zf: Starting")
						end
					else
						zflipstatus = 0                    
						xing = 0                
						gui.text(0, 70, "Zf: Waiting on twist (" .. zrotation .. ")")
					end
				else
					gui.text(0, 70, "Zf: Waiting for Tt to finish")
				end
			elseif zflipstatus == 1 then            
				if numzflips > completedzflips then
					xing = 0
					zwaited = 0
					completedzflips = numzflips
					if completedzflips >= thismaxzflips then
						if zwait2 == 0 then
							if twiststatus == 0 then
								if completedtwists < thismaxtwists then
									reverse = 1
									twiststatus = 1
									gui.text(0,50, "Tw: Z-flip caused reverse")
								end
							elseif twiststatus == 1 then
								if completedtwists < thismaxtwists then
									reverse = 1
									twiststatus = 1
									gui.text(0,50, "Tw: Z-flip caused reverse")
								end
							elseif twiststatus == 2 then
								if completedtwists < thismaxtwists then
									reverse = 1
									twiststatus = 1
									gui.text(0,50, "Tw: Z-flip caused reverse")
								end
							end                        
							zflipinplay = 2                        
						else
							zflipinplay = 0
							zfromthegrave = 2
							if completedtwists < thismaxtwists then
								twiststatus = 2
							end
						end
						zflipstatus = 0
						gui.text(0, 70, "Zf: Finished last one")                    
					else                    
						if zwait2 == 0 then
							zflipinplay = 3
							if completedtwists < thismaxtwists then
								twiststatus = 0
							end
							gui.text(0, 70, "Zf: Finished one, waiting")
							zflipstatus = 0                        
						else
							gui.text(0, 70, "Zf: Finished one mid-twist")
							zflipinplay = 0
							if completedtwists < thismaxtwists then
								twiststatus = 2
							end
							zflipstatus = 0
						end
						
					end
				else
					xing = 1
					gui.text(0, 70, "Zf: Continuing")
				end
			end
				
			if flipstatus == 0 then
				flipstatus = 0
				flipping = 0
				if numflips > completedflips then                
					backwardspaddles = 1
					completedflips = numflips
					if completedflips >= thismaxflips then
						flipping = 0
						flipstatus = 0
						gui.text(0, 80, "Fl: Finished last one")
						if rollwait == 0 then
							finalflipframe = curframe
						end
					else
						flipping = 1
						flipstatus = 1
						rollstatus = 0
						gui.text(0, 80, "Fl: Finished one, continuing")
					end
				else            
					if jumpstatus == 0 then
						gui.text(0, 80, "Fl: Still on ground")
					elseif (jumpstatus == 4 or completedflips >= thismaxflips) then
						gui.text(0, 80, "Fl: All done")
					elseif rollstatus == 1 then
						gui.text(0, 80, "Fl: Rolling instead")
					else
						gui.text(0, 80, "Fl: Starting")
						flipping = 1
						flipstatus = 1
					end
				end
			elseif flipstatus == 1 then
				flipping = 1
				if numflips > completedflips then                
					completedflips = numflips
					if completedflips >= thismaxflips then
						flipping = 0
						flipstatus = 0
						gui.text(0, 80, "Fl: Finished last one")
						if rollwait == 0 then
							finalflipframe = curframe
						end                        
					else
						gui.text(0, 80, "Fl: Finished one, continuing")
					end
				elseif (rollwait == 1 and curframe == finalflipframe - 1) then
					flipping = 0
					flipstatus = 3
					gui.text(0, 80, "Fl: Momentum will finish it")
				else
					gui.text(0, 80, "Fl: Continuing")
				end
			elseif flipstatus == 3 then
				if completedflips < thismaxflips then
					gui.text(0, 80, "Fl: Rollwait killed my dog!")
				else
					gui.text(0, 80, "Fl: All done thanks to rollwait")
				end
			end

			if rollstatus == 0 then
				rollstatus = 0
				rolling = 0
				if numrolls > completedrolls then
					backwardspaddles = 1
					completedrolls = numrolls
					if completedrolls >= thismaxrolls then
						rolling = 0
						rollstatus = 0
						gui.text(0, 90, "Ro: Finished last one")
					else
						rolling = 1
						flipstatus = 0
						rollstatus = 1
						gui.text(0, 90, "Ro: Finished one, continuing")
					end
				else            
					if jumpstatus == 0 then
						gui.text(0, 90, "Ro: Still on ground")
					elseif (jumpstatus == 4 or completedrolls >= thismaxrolls) then
						gui.text(0, 90, "Ro: All done")
					elseif flipstatus == 1 then
						gui.text(0, 90, "Ro: Flipping instead")
					else
						gui.text(0, 90, "Ro: Starting")
						rolling = 1
						rollstatus = 1
					end
				end
			elseif rollstatus == 1 then
				rolling = 1
				if numrolls > completedrolls then
					completedrolls = numrolls
					if completedrolls >= thismaxrolls then
						rolling = 0
						rollstatus = 0
						gui.text(0, 90, "Ro: Finished last one")
					else
						gui.text(0, 90, "Ro: Finished one, continuing")
					end
				else
					gui.text(0, 90, "Ro: Continuing")
				end
			end
			
			if zflipstatus > 0 and (rolling == 0 and flipping == 0) then
				if zflippreference == 0 then
					flipping = 1
				else
					rolling = 1
				end
			end
			
			if zflipinplay > 0 then
				zflipinplay = zflipinplay - 1
			end
			
			if backwardspaddles == 1 or reversefliproll == 1 then
				if rolling == 1 then
					flipping = 1
					rolling = 0
				elseif flipping == 1 then
					rolling = 1
					flipping = 0
				end
			end
					
			if (afterframe >= searchwindow or (curframe >= infiniteloopdetection) or (strategy == 4 and jumpstatus == 4)) then
				thisboostmeter = 0
				if completedtwists >= 8 then
					thisboostmeter = thisboostmeter + 200
				elseif completedtwists >= 6 then
					thisboostmeter = thisboostmeter + 176
				elseif completedtwists >= 4 then
					thisboostmeter = thisboostmeter + 152
				elseif completedtwists >= 2 then
					thisboostmeter = thisboostmeter + 128
				end
				if completedtabletops >= 1 then
					thisboostmeter = thisboostmeter + 152
				end
				if completedzflips == 1 then
					thisboostmeter = thisboostmeter + 128
				elseif completedzflips == 2 then
					thisboostmeter = thisboostmeter + 152
				elseif completedzflips == 3 then
					thisboostmeter = thisboostmeter + 176
				elseif completedzflips >= 4 then
					thisboostmeter = thisboostmeter + 200
				end
				if completedrolls == 1 then
					thisboostmeter = thisboostmeter + 128
				elseif completedrolls == 2 then
					thisboostmeter = thisboostmeter + 152
				elseif completedrolls == 3 then
					thisboostmeter = thisboostmeter + 176
				elseif completedrolls >= 4 then
					thisboostmeter = thisboostmeter + 200
				end
				if completedflips == 1 then
					thisboostmeter = thisboostmeter + 176
				elseif completedflips == 2 then
					thisboostmeter = thisboostmeter + 200
				elseif completedflips == 3 then
					thisboostmeter = thisboostmeter + 224
				elseif completedflips >= 4 then
					thisboostmeter = thisboostmeter + 248
				end
				lastspeed = curspeed * horzdirection * changedirection            
				if lastspeed < 0 then
					thisboostmeter = 0
				end
				if realboostmeter == 0 then
					thisboostmeter = 0
				end

				lastboost = thisboostmeter            
							
				finalscore = thisboostmeter + lastspeed
				if ycoordinate > maximumy then
					gui.text(0, 170, ycoordinate .. " above " .. maximumy)
					finalscore = -9999
				elseif ycoordinate < minimumy then
					gui.text(0, 170, ycoordinate .. " below " .. minimumy)
					finalscore = -9999
				end
				 
				if finalscore > bestfinalscore then
					rutcounter = 0
				else
					rutcounter = rutcounter + 1            
				end
				if (finalscore >= bestfinalscore) then                
					bestfinalscore = finalscore
					bestspeed = lastspeed                
					bestscoringtwists = thismaxtwists
					bestscoringtabletops = thismaxtabletops
					bestscoringzflips = thismaxzflips
					bestscoringrolls = thismaxrolls
					bestscoringflips = thismaxflips
					bestscoringtwistwait = twistwait
					bestscoringframewait = framewait
					bestscoringtabletopextrawait = tabletopextrawait
					bestscoringzwait = zwait
					bestscoringzwait2 = zwait2
					bestscoringtwistregisters = twistregisters
					bestscoringrollwait = rollwait
					bestscoringfinalflipframe = finalflipframe
				end

				if strategy == 1 then
					if trickexecution == 1 then                    
						if completedzflips == 0 and thismaxzflips > 0 and zwait == 0 then
							strategytext = "Try that again with zwait"
							zwait = 1
						elseif rollwait == 0 and thismaxrolls >= 1 and thismaxflips >= 1 then
							rollwait = 1
							strategytext = "Frame shaving with rollwait!"
						else
							if rollwait == 1 and thismaxrolls >= 1 and thismaxflips >= 1 and (completedrolls == 0 or completedflips == 0) then
								rollwait = 0
							end
							strategytext = "Executing specified trick!"
							strategy = 4
						end               
					elseif finalscore > lastscore then                    
						if lastaddition == 0 then
							if completedzflips == 0 and thismaxzflips > 0 and zwait == 0 then
								strategytext = "Guess fixed, try with zwait"
								lastaddition = 0
								zwait = 1
							elseif completedrolls == 0 and thismaxrolls > 0 and rollwait == 0 then
								strategytext = "Guess fixed, try with rollwait"
								lastaddition = 0
								rollwait = 1
							else
								lastaddition = 1
								strategytext = "Guess fixed, try Twist"
								thismaxtwists = completedtwists + 1
								if wholetwistsonly == 1 then
									thismaxtwists = thismaxtwists + 1
								end
								thismaxtabletops = completedtabletops                            
								thismaxzflips = math.min(4, completedzflips)
								thismaxrolls = math.min(4, completedrolls)
								thismaxflips = math.min(4, completedflips)
							end                                                    
						elseif (lastaddition == 1 and completedtwists >= thismaxtwists) then
							lastaddition = 1
							thismaxtwists = thismaxtwists + 1
							if wholetwistsonly == 1 then
								thismaxtwists = thismaxtwists + 1
							end
							strategytext = "Twist worked, add another"
							consecutivefailures = 0
						elseif (lastaddition == 1 and completedtwists < thismaxtwists) then
							thismaxtwists = completedtwists
							if thismaxtabletops == 0 then
								strategytext = "Unneeded Tw, Add Tt"
								lastaddition = 2
								thismaxtabletops = thismaxtabletops + 1
							else
								strategytext = "Unneeded Tw, Add Flip"
								lastaddition = 3
								thismaxflips = thismaxflips + 1
								rollwait = 0
							end
							consecutivefailures = consecutivefailures + 1
						elseif lastaddition == 2 then                        
							if (thismaxflips > 0) and (thismaxrolls == 0) then
								strategytext = "Tt worked, add Roll"
								lastaddition = 4
								thismaxrolls = thismaxrolls + 1
							else
								strategytext = "Tt worked, add Flip"
								lastaddition = 3
								thismaxflips = thismaxflips + 1
								rollwait = 0
							end
							consecutivefailures = 0
						elseif (lastaddition == 3 and completedflips+1 >= thismaxflips) then
							strategytext = "Flip worked, add Roll"
							lastaddition = 4
							thismaxrolls = thismaxrolls + 1
							consecutivefailures = 0
						elseif (lastaddition == 3 and completedflips+1 < thismaxflips) then
							thismaxflips = completedflips + 1
							strategytext = "Unneeded flip, add Roll"
							lastaddition = 4
							thismaxrolls = thismaxrolls + 1
							rollwait = 0
						elseif (lastaddition == 4 and completedrolls+1 >= thismaxrolls) then                    
							strategytext = "Roll worked, add Zflip"
							lastaddition = 5
							thismaxzflips = thismaxzflips + 1                        
							consecutivefailures = 0
						elseif (lastaddition == 4 and completedrolls+1 < thismaxrolls) then
							if rollwait == 0 then
								strategytext = "Try that again with rollwait"
								rollwait = 1
							else
								thismaxrolls = completedrolls + 1
								strategytext = "Unneeded roll, add Zflip"
								lastaddition = 5
								thismaxzflips = thismaxzflips + 1
							end
						elseif (lastaddition == 5 and completedzflips >= thismaxzflips) then                    
							strategytext = "Zflip worked, add twist"
							lastaddition = 1
							thismaxtwists = thismaxtwists + 1
							if wholetwistsonly == 1 then
								thismaxtwists = thismaxtwists + 1
							end
							consecutivefailures = 0
						elseif (lastaddition == 5 and completedzflips < thismaxzflips) then
							if (thismaxzflips == 1 and zwait == 0) then
								strategytext = "Try that again with zwait"
								zwait = 1                            
							else
								strategytext = "Uneeded Zf, add twist"
								thismaxzflips = completedzflips
								lastaddition = 1
								thismaxtwists = thismaxtwists + 1
								if wholetwistsonly == 1 then
									thismaxtwists = thismaxtwists + 1
								end
							end
						elseif (lastaddition == 6 or lastaddition == 7) then
							strategytext = "F+R worked, add zflip"
							lastaddition = 5
							thismaxzflips = thismaxzflips + 1                        
							consecutivefailures = 0                    
						end
					else
						if rollwait == 0 and thismaxrolls >= 1 and thismaxflips >= 1 then
							if lastaddition == 5 and completedzflips < thismaxzflips and thismaxzflips == 1 and zwait == 0 then
								strategytext = "Try that again with zwait"
								zwait = 1
								consecutivefailures = consecutivefailures - 1
							else                     
								rollwait = 1
								strategytext = "Try that with rollwait!"
							end
						elseif rollwait == 1 and thismaxrolls >= 1 and thismaxflips >= 1 and (completedflips < thismaxflips) and lastaddition < 6 then
							rollwait = -1
							strategytext = "Rollwait was a failure!"
							if rutcounter > ruttolerance - 3 then
								if thismaxflips + 1 < thismaxrolls then
									thismaxrolls = thismaxrolls - 1
									thismaxflips = thismaxflips + 1
									lastaddition = 3
									strategytext = "Trade a roll for a flip"
								elseif thismaxrolls + 1 < thismaxflips then
									thismaxflips = thismaxflips - 1
									thismaxrolls = thismaxrolls + 1
									lastaddition = 4
									strategytext = "Trade a flip for a roll"
								end
							end
						else
							consecutivefailures = consecutivefailures + 1
							if lastaddition == 0 then
								if completedzflips == 0 and thismaxzflips > 0 and zwait == 0 then
									strategytext = "Guess fixed, try with zwait"
									lastaddition = 0
									zwait = 1
								elseif completedrolls == 0 and thismaxrolls > 0 and rollwait == 0 then
									strategytext = "Guess fixed, try with rollwait"
									lastaddition = 0
									rollwait = 1                            
								else
									lastaddition = 1
									strategytext = "Guess fixed, try Twist"
									thismaxtwists = completedtwists + 1
									if wholetwistsonly == 1 then
										thismaxtwists = thismaxtwists + 1
									end
									thismaxtabletops = completedtabletops                            
									thismaxzflips = math.min(4, completedzflips)
									thismaxrolls = math.min(4, completedrolls)
									thismaxflips = math.min(4, completedflips)                                                
								end 
							elseif lastaddition == 1 then
								thismaxtwists = thismaxtwists - 1
								if wholetwistsonly == 1 then
									thismaxtwists = thismaxtwists - 1
								end
								if thismaxtabletops == 0 then
									strategytext = "Twist failed, add Tt"
									lastaddition = 2
									thismaxtabletops = thismaxtabletops + 1
								else
									strategytext = "Twist failed, add Flip"
									lastaddition = 3
									thismaxflips = thismaxflips + 1
									rollwait = 0
								end
							elseif lastaddition == 2 then
								strategytext = "Tt failed, try Flip"
								thismaxtabletops = thismaxtabletops - 1
								lastaddition = 3
								thismaxflips = thismaxflips + 1
								rollwait = 0
							elseif lastaddition == 3 then
								if completedflips+1 < thismaxflips then
									thismaxflips = completedflips + 1
									strategytext = "Un. Flip failed, try extra Roll"
								else
									strategytext = "Flip failed, try extra Roll"
								end                        
								lastaddition = 6
								thismaxrolls = thismaxrolls + 1                    
								consecutivefailures = consecutivefailures - 1
							elseif lastaddition == 4 then
								if rollwait == 0 then 
									strategytext = "Try that again with rollwait"
									rollwait = 1                        
									consecutivefailures = consecutivefailures - 1
								else
									if completedrolls+1 < thismaxrolls then
										thismaxrolls = completedrolls + 1
										strategytext = "Un. Roll failed, try extra Flip"
									else
										strategytext = "Roll failed, try extra Flip"
									end
									thismaxflips = thismaxflips + 1
									rollwait = 0
									lastaddition = 7                        
									consecutivefailures = consecutivefailures - 1
								end
							elseif lastaddition == 5 then
								if completedzflips < thismaxzflips then
									if (thismaxzflips == 1 and zwait == 0) then
										strategytext = "Try that again with zwait"
										zwait = 1
										consecutivefailures = consecutivefailures - 1
									else
										thismaxzflips = completedzflips
										strategytext = "Un. Zf failed, add Twist"
										lastaddition = 1
										thismaxtwists = thismaxtwists + 1
										if wholetwistsonly == 1 then
											thismaxtwists = thismaxtwists + 1
										end
									end
								else
									thismaxzflips = thismaxzflips - 1
									strategytext = "Zflip failed, add Twist"
									lastaddition = 1
									thismaxtwists = thismaxtwists + 1
								end
							elseif lastaddition == 6 then
								if rollwait == 0 then 
									strategytext = "Try that again with rollwait"
									rollwait = 1                        
									consecutivefailures = consecutivefailures - 1
								else
									strategytext = "F+R failed, try Roll only"                            
									thismaxflips = thismaxflips - 1
									lastaddition = 4
								end
							elseif lastaddition == 7 then
								if rollwait == 0 then 
									strategytext = "Try that again with rollwait"
									rollwait = 1                        
									consecutivefailures = consecutivefailures - 1
								else                        
									strategytext = "Roll and Flip failed, add zflip"
									thismaxrolls = thismaxrolls - 1
									thismaxflips = thismaxflips - 1
									lastaddition = 5
									thismaxzflips = thismaxzflips + 1                        
								end
							end
						end                  
					end
					if (consecutivefailures >= 4 or rutcounter >= ruttolerance) then                                                        
						--strategy = 2
						--thismaxtwists = 1
						--thismaxtabletops = 0
						--thismaxzflips = 0
						--thismaxrolls = 0
						--thismaxflips = 0
						--lastscore = 0
						--lastaddition = 1
						--consecutivefailures = 0                    
						--maxtwistonly = 0
						--maxtabletopsonly = 0
						--maxzflipsonly = 0
						--maxrollsonly = 0
						--maxflipsonly = 0                    
						-- ----------------
						if framewait >= maxframewait then
							strategy = 4
							thismaxtwists = bestscoringtwists
							thismaxtabletops = bestscoringtabletops
							thismaxzflips = bestscoringzflips
							thismaxrolls = bestscoringrolls
							thismaxflips = bestscoringflips
							twistwait = bestscoringtwistwait
							framewait = bestscoringframewait
							tabletopextrawait = bestscoringtabletopextrawait
							zwait = bestscoringzwait
							zwait2 = bestscoringzwait2
							twistregisters = bestscoringtwistregisters
							rollwait = bestscoringrollwait
							finalflipframe = bestscoringfinalflipframe
							lastscore = 0
							lastaddition = 0
							consecutivefailures = 0
							rutcounter = 0                                   
							snes9x.speedmode("normal")                            
						else
							
							framewait = framewait + frameincrement                        
							mode = 1                    
						end
					end
					reload = 1
				elseif strategy == 2 then
					if finalscore > lastscore then                    
						if lastaddition == 1 then
							lastaddition = 1
							thismaxtwists = thismaxtwists + 1
						elseif lastaddition == 2 then
							lastaddition = 3
							maxtabletopsonly = thismaxtabletops
							thismaxtabletops = 0
							thismaxflips = thismaxflips + 1
						elseif lastaddition == 3 then
							lastaddition = 3
							thismaxflips = thismaxflips + 1
						elseif lastaddition == 4 then
							lastaddition = 4
							thismaxrolls = thismaxrolls + 1
						elseif lastaddition == 5 then
							lastaddition = 5
							thismaxzflips = thismaxzflips + 1
						end                    
					else                    
						if lastaddition == 1 then
							maxtwistonly = thismaxtwists - 1
							thismaxtwists = 0
							lastaddition = 2
							thismaxtabletops = 1
						elseif lastaddition == 2 then
							maxtabletopsonly = thismaxtabletops - 1
							thismaxtabletops = 0
							lastaddition = 3
							thismaxflips = thismaxflips + 1
						elseif lastaddition == 3 then
							maxflipsonly = thismaxflips - 1
							thismaxflips = 0
							lastaddition = 4
							thismaxrolls = thismaxrolls + 1                    
						elseif lastaddition == 4 then
							maxrollsonly = thismaxrolls - 1
							thismaxrolls = 0
							lastaddition = 5
							thismaxzflips = thismaxzflips + 1                        
						elseif lastaddition == 5 then
							maxzflipsonly = thismaxzflips - 1
							strategy = 3
							thismaxtwists = maxtwistonly
							thismaxtabletops = maxtabletopsonly
							thismaxzflips = maxzflipsonly
							thismaxrolls = maxrollsonly
							thismaxflips = maxflipsonly
							lastfinalscore = 0
							if thismaxrolls > 4 then
								lastaddition = 4
							elseif thismaxzflips > 4 then
								lastaddition = 5
							elseif thismaxflips > 4 then
								lastaddition = 3
							elseif thismaxtwists > 4 then
								lastaddition = 1
							elseif thismaxrolls > 1 then
								lastaddition = 4
							elseif thismaxzflips > 1 then
								lastaddition = 5
							elseif thismaxflips > 1 then
								lastaddition = 3
							elseif thismaxtwists > 1 then
								lastaddition = 1
							elseif thismaxrolls > 0 then
								lastaddition = 4
							elseif thismaxzflips > 0 then
								lastaddition = 5
							elseif thismaxflips > 0 then
								lastaddition = 3
							elseif thismaxtabletops > 0 then
								lastaddition = 2
							elseif thismaxtwists > 0 then
								lastaddition = 1
							else
								lastaddition = 6 -- error condition
							end
							
							consecutivefailures = 0
						end                    
					end
				elseif strategy == 3 then
					if (finalscore > lastscore or lastaddition == 6) then
						if (consecutivefailures > 1 or (consecutivefailures == 0 and lastaddition == 1)) then
							thismaxtwists = thismaxtwists + 1
							lastaddition = 1
						else
							if framewait >= maxframewait then
								strategy = 4
								thismaxtwists = bestscoringtwists
								thismaxtabletops = bestscoringtabletops
								thismaxzflips = bestscoringzflips
								thismaxrolls = bestscoringrolls
								thismaxflips = bestscoringflips
								twistwait = bestscoringtwistwait
								framewait = bestscoringframewait
								tabletopextrawait = bestscoringtabletopextrawait
								twistregisters = bestscoringtwistregisters
								rollwait = bestscoringrollwait
								finalflipframe = bestscoringfinalflipframe
								snes9x.speedmode("normal")                            
							else
								framewait = framewait + frameincrement
								mode = 1
							end
						end                        
						consecutivefailures = 0
					else
						consecutivefailures = consecutivefailures + 1
						if (consecutivefailures == 1 and lastaddition == 1) then
							lastaddition = 1
						elseif thismaxrolls > 4 then
							lastaddition = 4
						elseif thismaxzflips > 4 then
							lastaddition = 5
						elseif thismaxflips > 4 then
							lastaddition = 3
						elseif thismaxtwists > 4 then
							lastaddition = 1
						elseif thismaxrolls > 1 then
							lastaddition = 4
						elseif thismaxzflips > 1 then
							lastaddition = 5
						elseif thismaxflips > 1 then
							lastaddition = 3
						elseif thismaxtwists > 1 then
							lastaddition = 1
						elseif thismaxrolls > 0 then
							lastaddition = 4
						elseif thismaxzflips > 0 then
							lastaddition = 5
						elseif thismaxflips > 0 then
							lastaddition = 3
						elseif thismaxtabletops > 0 then
							lastaddition = 2
						elseif thismaxtwists > 0 then
							lastaddition = 1
						else
							lastaddition = 6
						end
						
						if lastaddition == 1 then
							maxtwistonly = thismaxtwists - 1
						elseif lastaddition == 2 then
							maxtabletopsonly = thismaxtabletops - 1
						elseif lastaddition == 3 then
							maxflipsonly = thismaxflips - 1
						elseif lastaddition == 4 then
							maxrollsonly = thismaxrolls - 1
						elseif lastaddition == 5 then
							maxzflipsonly = thismaxzflips - 1
						end                    
					end                
				elseif strategy == 4 then
					mode = 5
				end
				lastscore = finalscore
				reload = 1
				if mode == 5 then
					reload = 0
				end
			end        
			
		elseif mode == 5 then
			
		end
		
		buttontable = {start=nil, select=nil, up=nil, down=nil, left=nil, right=nil, A=nil, B=nil, X=nil, Y=nil, L=nil, R=nil}

		if reverse == 0 then
			if horzdirection == 1 then
				buttontable.right = true
			else
				buttontable.left = true
			end
		else
			if horzdirection == 1 then
				buttontable.left = true
			else
				buttontable.right = true
			end
		end
		
		if flipping == 1 then
			if horzdirection == 1 then
				buttontable.R = true
			else
				buttontable.L = true
			end
		elseif rolling == 1 then
			if horzdirection == 1 then
				buttontable.L = true
			else
				buttontable.R = true
			end
		elseif (mode > 3 and thisflipovercorrect > 0) then
			gui.text(0,140,"FLIP OVERCORRECT")
			thisflipovercorrect = thisflipovercorrect - 1
			if horzdirection == 1 then
				buttontable.R = true
			else
				buttontable.L = true
			end    
		elseif (mode > 3 and thisrollovercorrect > 0) then
			gui.text(0,140,"ROLL OVERCORRECT")
			thisrollovercorrect = thisrollovercorrect - 1
			if horzdirection == 1 then
				buttontable.L = true
			else
				buttontable.R = true
			end        
		end
		
		if jumping == 1 then
			if maxBframes == 0 then
				buttontable.B = true
			elseif curframe < maxBframes then
				buttontable.B = true        
			end
		end    
		
		if xing == 1 then
			buttontable.X = true
		end
		
		lastframetwist = numtwists
		lastframetabletop = numtabletops   
		
		joypad.set(1, buttontable)
		curframe = curframe + 1
		snes9x.frameadvance()
	end

	local tricktext = ""
	if completedtabletops > 0 then
		tricktext = tricktext .. "Tt"
	end
	if completedflips > 1 then
		tricktext = tricktext .. completedflips .. "F"
	elseif completedflips > 0 then
		tricktext = tricktext .. "F"    
	end
	if completedrolls > 1 then
		tricktext = tricktext .. completedrolls .. "R"
	elseif completedrolls > 0 then
		tricktext = tricktext .. "R"    
	end
	if completedtwists > 2 then
		tricktext = tricktext .. math.floor(completedtwists/2) .. "T"
	elseif completedtwists > 0 then
		tricktext = tricktext .. "T"    
	end
	if completedzflips > 1 then
		tricktext = tricktext .. completedzflips .. "Z"
	elseif completedzflips > 0 then
		tricktext = tricktext .. "Z"    
	end
	gui.text(0, 10, "ALL DONE: " .. tricktext)
	gui.text(0, 20, "Tried: " .. thismaxtabletops .. "Tt " .. thismaxflips .. "F " .. thismaxrolls .. "R " .. thismaxtwists/2 .. "T " .. thismaxzflips .. "Z")
	gui.text(0, 30, "Made : " .. completedtabletops .. "Tt " .. completedflips .. "F " .. completedrolls .. "R " .. completedtwists/2 .. "T " .. completedzflips .. "Z")
	gui.text(0, 40, "Framewait: " .. framewait)
	gui.text(0, 50, "Twistwait: " .. twistwait)
	gui.text(0, 60, "Twistregisters: " .. twistregisters)
	gui.text(0, 70, "Tabletopextrawait: " .. tabletopextrawait)
	gui.text(0, 80, "zwait: " .. zwait)
	gui.text(0, 90, "zwait2: " .. zwait2)
	gui.text(0, 100, "finalflipframe: " .. finalflipframe)
	gui.text(0, 110, "rollwait: " .. rollwait)
	gui.text(0, 120, "Resulting speed: " .. bestspeed)
end

main()
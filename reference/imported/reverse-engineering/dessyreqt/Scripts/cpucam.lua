RAM = {
    address = 0x7E2081
}

while true do
    memory.writebyte(RAM.address, 1);
    emu.frameadvance();
end
    

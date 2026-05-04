from pathlib import Path
import pygame as pg
from time import sleep
RegisterFile = {
    0b0000: 0,
    0b0001: 0,
    0b0010: 0,
    0b0011: 0,
    0b0100: 0,
    0b0101: 0,
    0b0110: 0,
    0b0111: 0,
    0b1000: 0,
    0b1001: 0,
    0b1010: 0,
    0b1011: 0,
    0b1100: 0,
    0b1101: 0,
    0b1110: 0,
    0b1111: 0
}
JpFlags = {
    "eq":  1,
    "ne":  0,
    "lt":  0,
    "le":  1,
    "gt":  0,
    "ge":  1,
    "sl":  0,
    "sle": 1,
    "sg":  0,
    "sge": 1
}
PC = 0
FetchedInstruction = 0
DecodedInstruction = 0
GBiFlag = 0
jump = 0

RAM = [0] * 0x3fff
VRAM = [0] * 0x1fff
ROM = [0] * 0x3fff

InOutROM = [5]
InOutIndex = -1

skip = True
ROMData = Path("C:/Users/Karamat/Python prjects/HexDump.txt").read_text() if skip else False

ColourLookup = []
for i in range(256):
    RedVal = (i >> 5) & 0x07
    GreenVal = (i >> 2) & 0x07
    BlueVal = i & 0x03
    RedVal = (RedVal * 255) // 7
    GreenVal = (GreenVal * 255) // 7
    BlueVal = (BlueVal * 255) // 3
    ColourLookup.append((RedVal, GreenVal, BlueVal))

while not skip:
    print("Enter the file path of the hex dump")
    FilePathForASM = input()
    FilePathForASM = FilePathForASM.replace('"', "")
    try:
        FilePath = Path(FilePathForASM)
        ROMData = FilePath.read_text()
        break
    except:
        print("Error handling file path")
        continue
ROMData = ROMData.replace("\n", " ")
ROMData = ROMData.split(" ")
for i in range(0, len(ROMData)):
    ROMData[i] = int(ROMData[i], 16)
for address, byte in enumerate(ROMData):
    ROM[address] = byte



def cmp(A, B, iFlag=0):
    global JpFlags
    if not iFlag:
        A &= 0xffff
        B &= 0xffff
        JpFlags["eq"] = A == B
        JpFlags["ne"] = A != B
        JpFlags["lt"] = A <  B
        JpFlags["le"] = A <= B
        JpFlags["gt"] = A >  B
        JpFlags["ge"] = A >= B
        A = A^0x8000
        B = B^0x8000
        JpFlags["sl"] =  A <  B
        JpFlags["sle"] = A <= B
        JpFlags["sg"] =  A >  B
        JpFlags["sge"] = A >= B

def ALU(OpA, OpB, ArOp=0, JpOp=0):
    iFlag = GBiFlag
    match ArOp:
        case 2:
            return (RegisterFile[OpA] & RegisterFile[OpB] if not iFlag else RegisterFile[OpA] & OpB) & 0xffff
        case 3:
            return (RegisterFile[OpA] | RegisterFile[OpB] if not iFlag else RegisterFile[OpA] | OpB) & 0xffff
        case 1: 
            return (~(RegisterFile[OpA] & RegisterFile[OpB]) if not iFlag else ~(RegisterFile[OpA] & OpB)) & 0xffff
        case 4:
            return (~(RegisterFile[OpA] | RegisterFile[OpB]) if not iFlag else ~(RegisterFile[OpA] | OpB))  & 0xffff
        case 5:
            return (RegisterFile[OpA] ^ RegisterFile[OpB] if not iFlag else RegisterFile[OpA] ^ OpB) & 0xffff
        case 6:
            return (RegisterFile[OpA] + RegisterFile[OpB] if not iFlag else RegisterFile[OpA] + OpB) & 0xffff
        case 7:
            return (RegisterFile[OpA] - RegisterFile[OpB] if not iFlag else RegisterFile[OpA] - OpB) & 0xffff
        case 8:
            return (RegisterFile[OpA] * RegisterFile[OpB] if not iFlag else RegisterFile[OpA] * OpB) & 0xffff
        case 9:
            return (RegisterFile[OpA] // RegisterFile[OpB] if not iFlag else RegisterFile[OpA] // OpB) & 0xffff
        case 10:
            return (RegisterFile[OpA] % RegisterFile[OpB] if not iFlag else RegisterFile[OpA] % OpB) & 0xffff
        case 11:
            return (RegisterFile[OpA] << RegisterFile[OpB] if not iFlag else RegisterFile[OpA] << OpB) & 0xffff
        case 12:
            return (RegisterFile[OpA] >> RegisterFile[OpB] if not iFlag else RegisterFile[OpA] >> OpB) & 0xffff
        case 13:
            if not RegisterFile[OpA] & 0x8000:
                return RegisterFile[OpA] >> RegisterFile[OpB] if not iFlag else RegisterFile[OpA] >> OpB
            else:
                if not iFlag:
                    FinalNum = 0
                    for i in range(RegisterFile[OpB]):
                        FinalNum = RegisterFile[OpA] >> i + 0x8000
                else:
                    FinalNum = 0
                    for i in range(OpB):
                        FinalNum = RegisterFile[OpA] >> i + 0x8000
            return FinalNum & 0xffff
    match JpOp:
        case 0:
            return 0
        case 7:
            if not iFlag:
                cmp(RegisterFile[OpA], RegisterFile[OpB])
            else:
                cmp(RegisterFile[OpA], OpB)
            return 0
        case 1:
            return JpFlags["eq"]
        case 2: 
            return JpFlags["ne"]
        case 3:
            return JpFlags["lt"]
        case 4:
            return JpFlags["le"]
        case 5:
            return JpFlags["gt"]
        case 6:
            return JpFlags["ge"]
        case 8:
            return JpFlags["sl"]
        case 9:
            return JpFlags["sle"]
        case 10:
            return JpFlags["sg"]
        case 11:
            return JpFlags["sge"]

def MemControl(addr, val, mode):
    global RAM
    try:
        if mode:
            RAM[(addr)+1 % 0x3fff] = val & 0x00ff
            RAM[addr % 0x3fff] = val & 0xff00
        else:
            return (RAM[addr]<<16) | RAM[addr+1]
    except:
        print(hex(fetch(PC-4)))
        exit()

def VidMemControl(addr, val, mode): 
    match mode:
        case 0:
            return VRAM[addr] & 0xff
        case 1:
            return VRAM[addr+1]<<16 | VRAM[addr]
        case 2:
            VRAM[addr % 0x1fff] = val & 0xff
        case 3:
            VRAM[addr % 0x1fff] = val & 0x00ff
            VRAM[(addr+1) % 0x1fff] = val & 0xff00

def InOut(Dout, mode):
    global PC, InOutIndex
    match mode:
        case 1:
            return InOutROM[InOutIndex]
        case 2: InOutIndex = Dout
        case 3: return PC
        case 4: PC = Dout-4
        case 5: return 0

def fetch(addr):
    FetchedData = 0
    FetchedData |= ROM[addr] << 24
    FetchedData |= ROM[addr+1] << 16
    FetchedData |= ROM[addr+2] << 8
    FetchedData |= ROM[addr+3]
    return FetchedData
def decode(MachineCode):
    global GBiFlag
    GBiFlag = (MachineCode & (1 << 24)) >> 24
    mode = (MachineCode & (0x7 << 29)) >> 29
    opcode = (MachineCode & (0xf << 25)) >> 25
    dst = (MachineCode & (0xf << 20)) >> 20
    OpA = (MachineCode & (0xf << 16)) >> 16
    OpB = (MachineCode & (0xf << 8)) >> 8
    immediate = MachineCode & 0xffff
    return (mode, opcode, dst, OpA, OpB, immediate)

pg.init()
width, height = 80, 72
ScaleFactor = 8
canvas = pg.Surface((width, height))
screen = pg.display.set_mode((width*ScaleFactor, height*ScaleFactor))
pg.display.set_caption("M16 G4 DISP")

def DrawFrame():
    Parray = pg.PixelArray(canvas)

    for y in range(height):
        for x in range(width):
            addr = y * width + x
            ColourIndex = VRAM[addr] & 0xff
            Parray[x, y] = ColourLookup[ColourIndex]
    del Parray
    ScaledWindow = pg.transform.scale(canvas, (width * ScaleFactor, height * ScaleFactor))
    screen.blit(ScaledWindow, (0, 0))
    pg.display.flip()

counter = 0
while True:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()
            exit()
    RegisterFile[0] = 0
    FetchedInstruction = fetch(PC)
    DecodedInstruction = decode(FetchedInstruction)
    if DecodedInstruction == (0, 0, 0, 0, 0, 255):
        PC += 4
        continue
    elif DecodedInstruction == (0, 0, 0, 0, 0, 1):
        exit()
    match DecodedInstruction[0]:
        case 0:
            if GBiFlag:
                RegisterFile[DecodedInstruction[2]] = ALU(DecodedInstruction[3], DecodedInstruction[5], DecodedInstruction[1])
            else:
                RegisterFile[DecodedInstruction[2]] = ALU(DecodedInstruction[3], DecodedInstruction[4], DecodedInstruction[1])
        case 1:
            if not GBiFlag:
                jump = ALU(DecodedInstruction[3], DecodedInstruction[4], 0, DecodedInstruction[1])
            else:
                jump = ALU(DecodedInstruction[3], DecodedInstruction[5], 0, DecodedInstruction[1])
            if jump:
                PC = DecodedInstruction[5] - 4
        case 2:
            if DecodedInstruction[1] & 1 == 1:
                RegisterFile[DecodedInstruction[2]] = InOut(0, DecodedInstruction[1])
            else:
                if GBiFlag:
                    InOut(DecodedInstruction[5], DecodedInstruction[1])
                else:
                    InOut(RegisterFile[DecodedInstruction[4]], DecodedInstruction[1])
        case 3:
            if not GBiFlag:
                match DecodedInstruction[1]:
                    case 1:
                        RegisterFile[DecodedInstruction[2]] = MemControl(RegisterFile[DecodedInstruction[4]], None, 0)
                    case 2:
                        MemControl(RegisterFile[DecodedInstruction[4]], RegisterFile[DecodedInstruction[3]], 1)
                    case 3:
                        RegisterFile[DecodedInstruction[2]] = VidMemControl(RegisterFile[DecodedInstruction[4]], None, 0)
                    case 4:
                        RegisterFile[DecodedInstruction[2]] = VidMemControl(RegisterFile[DecodedInstruction[4]], None, 1)
                    case 5:
                        VidMemControl(RegisterFile[DecodedInstruction[4]], RegisterFile[DecodedInstruction[3]], 2)
                    case 6:
                        VidMemControl(RegisterFile[DecodedInstruction[4]], RegisterFile[DecodedInstruction[3]], 3)
            else:
                match DecodedInstruction[1]:
                    case 1:
                        RegisterFile[DecodedInstruction[2]] = MemControl(DecodedInstruction[5], None, 0)
                    case 2:
                        MemControl(DecodedInstruction[5], RegisterFile[DecodedInstruction[3]], 1)
                    case 3:
                        RegisterFile[DecodedInstruction[2]] = VidMemControl(DecodedInstruction[5], None, 0)
                    case 4:
                        RegisterFile[DecodedInstruction[2]] = VidMemControl(DecodedInstruction[5], None, 1)
                    case 5:
                        VidMemControl(DecodedInstruction[5], RegisterFile[DecodedInstruction[3]], 2)
                    case 6:
                        VidMemControl(DecodedInstruction[5], RegisterFile[DecodedInstruction[3]], 3)

    PC += 4
    if PC >= 0x3ffb:
        PC = 0
    counter += 1
    if counter >= 1:
        DrawFrame()
        counter = 0
    print(RAM[12288:12290])
    print(PC)
    print(RegisterFile)
    print(DecodedInstruction)
    input()
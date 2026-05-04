from pathlib import Path
from struct import pack

SrcFile = ""
DestFile = ""

skip = True
program = Path(SrcFile).read_text() if skip else False

while not skip:
    print("Enter the file path of the assembly (can be .txt)")
    FilePathForASM = input()
    FilePathForASM = FilePathForASM.replace('"', "")
    try:
        FilePath = Path(FilePathForASM)
        program = FilePath.read_text()
        break
    except:
        print("Error handling file path")
        continue

# Break the data into lines and strip
ProgramLines = program.split("\n")
for index, line in enumerate(ProgramLines):
    ProgramLines[index] = line.strip()

# Handle label indexing using a 3 pass system
# Pass 1: Assign clock values and identifiers to each line
ProgramCounter = 0
FinalProgram = []
labels = {}

for line in ProgramLines:
    if ":" not in line:
        FinalProgram.extend([("INSTRUCTION", line, ProgramCounter)])
        if "call" in line:
            ProgramCounter += 20
        elif "ret" in line:
            ProgramCounter += 12
        elif "push" in line or "pop" in line or "jmp" in line:
            ProgramCounter += 4
        ProgramCounter += 4
    if ":" in line:
        FinalProgram.extend([("LABEL", line.removesuffix(":"), ProgramCounter)])

# Pass 2: Fetch Label Data and sort by length
for LineData in FinalProgram:
    if LineData[0] == "LABEL":
        labels[LineData[1]] = LineData[2]
LabelNames = sorted(list(labels.keys()), key=len, reverse=True)
FinishedLabels = {}
for label in LabelNames:
    LabelVal = labels[label]
    FinishedLabels[label] = LabelVal
labels = FinishedLabels
del FinishedLabels

# Pass 3: Replace labels with their address
LabelNames = list(labels.keys())
ProgramLines = FinalProgram
FinalProgram = []
for LineNum, LineData in enumerate(ProgramLines):
    LabelMatched = False
    if LineData[0] == "LABEL":
        continue
    else:
        for LabelName in LabelNames:
            if LabelName in LineData[1]:
                LineData = LineData[1].replace(LabelName, f"{labels[LabelName]}")
                LabelMatched = True
    if not LabelMatched:
        LineData = LineData[1]
    FinalProgram.append(LineData)

# Break down instructions
BrokenProgram = []
for line in FinalProgram:
    line = line.replace(",", "]")
    line = line.replace("[", "]")
    line = line.replace("]", "")
    BrokenProgram.append(line.split(" "))

# Expand the program
ExpandedProgram = []
for index, BrokenLine in enumerate(BrokenProgram):
    NextLine = [BrokenLine]
    if BrokenLine[0] == "ret":
        NextLine = [
                    ["sub", "sp", "2", "sp"],
                    ["load", "sp", "r10"],
                    ["plock", "r10"]
                    ]

    elif BrokenLine[0] == "call":
        NextLine = [
                    ["glock", "r10"],
                    ["add", "r10", "24", "r10"],
                    ["store", "r10", "sp"],
                    ["add", "sp", "2", "sp"],
                    ["jne", BrokenLine[1]],
                    ["je", BrokenLine[1]]
                    ]

    elif BrokenLine[0] == "push":
        NextLine = [
                    ["store", BrokenLine[1], "sp"],
                    ["add", "sp", "2", "sp"]
                    ]

    elif BrokenLine[0] == "pop":
        NextLine = [
                    ["sub", "sp", "2", "sp"],
                    ["load", "sp", BrokenLine[1]]
                    ]

    elif BrokenLine[0] == "jmp":
        NextLine = [
                    ["jne", BrokenLine[1]],
                    ["je", BrokenLine[1]]
                    ]

    elif BrokenLine[0] == "mov":
        NextLine = [
                    ["or", "zr", BrokenLine[1], BrokenLine[2]]
                    ]

    elif BrokenLine[0] == "inc":
        NextLine = [
                    ["add", BrokenLine[1], BrokenLine[2], BrokenLine[1]]
                    ]

    elif BrokenLine[0] == "dec":
        NextLine = [
                    ["sub", BrokenLine[1], BrokenLine[2], BrokenLine[1]]
                    ]

    ExpandedProgram.extend(NextLine)

# Convert to Machine Code
registers = {
    "zr":  0b0000,
    "r1":  0b0001,
    "r2":  0b0010,
    "r3":  0b0011,
    "r4":  0b0100,
    "r5":  0b0101,
    "r6":  0b0110,
    "r7":  0b0111,
    "r8":  0b1000,
    "r9":  0b1001,
    "r10": 0b1010,
    "r11": 0b1011,
    "r12": 0b1100,
    "r13": 0b1101,
    "r14": 0b1110,
    "sp":  0b1111,
}

ArithmaticOpcodes = {
    "nand": 0b00000010,
    "and":  0b00000100,
    "or":   0b00000110,
    "nor":  0b00001000,
    "xor":  0b00001010,
    "add":  0b00001100,
    "sub":  0b00001110,
    "mul":  0b00010000,
    "div":  0b00010010,
    "mod":  0b00010100,
    "lsl":  0b00010110,
    "lsr":  0b00011000,
    "asr":  0b00011010
}

JumpOpcodes = {
    "cmp": 0b00101110,
    "je":  0b00100010,
    "jne": 0b00100100,
    "jl":  0b00100110,
    "jle": 0b00101000,
    "jg":  0b00101010,
    "jge": 0b00101100
}

InOutOpcodes = {
    "in":       0b01000010,
    "out":      0b01000100,
    "glock":    0b01000110,
    "plock":    0b01001000,
    "keyboard": 0b01001010
}

MemoryOpcodes = {
    "load":     0b01100010,
    "store":    0b01100100,
    "dload8":   0b01100110,
    "dload16":  0b01101000,
    "dstore8":  0b01101010,
    "dstore16": 0b01101100,
    "stm":      0b01101111,
    "spm":      0b01101111
}

OtherOpcodes = {
    "nop":   0xff,
    "hlt":   0x01,
    "sinit": 0x07f03000
}

HexString = ""
HexCount = 0
FinalHexString = "0x"

for instruction in ExpandedProgram:
    if instruction[0] in ArithmaticOpcodes:
        opcode = ArithmaticOpcodes[instruction[0]]
        OpA = registers[instruction[1]] << 16
        try:
            OpB = registers[instruction[2]]<<8
        except KeyError:
            OpB = int(instruction[2])
            opcode += 1
        dest = registers[instruction[3]] << 20
        InstructionValue = ((opcode<<24)|dest|OpA|OpB)
        HexString += pack(">I", InstructionValue).hex()
        continue

    elif instruction[0] in JumpOpcodes:
        opcode = JumpOpcodes[instruction[0]]
        if instruction[1].isdigit():
            opcode += 1
            OpA = int(instruction[1])
            InstructionValue = ((opcode<<24)|OpA)
            HexString += pack(">I", InstructionValue).hex()
            continue
        else:
            OpA = registers[instruction[1]] << 16
            try:
                OpB = registers[instruction[2]] << 8
            except:
                opcode += 1
                OpB = int(instruction[2])
            InstructionValue = ((opcode<<24)|OpA|OpB)
            HexString += pack(">I", InstructionValue).hex()
            continue

    elif instruction[0] in InOutOpcodes:
        opcode = InOutOpcodes[instruction[0]]
        dest = registers[instruction[1]] << 20
        if instruction[0] in ["plock", "out"]:
            dest = registers[instruction[1]] << 8
        InstructionValue = (opcode<<24)|dest
        HexString += pack(">I", InstructionValue).hex()
        continue

    elif instruction[0] in MemoryOpcodes:
        opcode = MemoryOpcodes[instruction[0]]
        if instruction[0] in ["load", "dload8", "dload16"]:
            OpA = registers[instruction[2]] << 20
            try:
                OpB = registers[instruction[1]] << 8
            except KeyError:
                opcode += 1
                OpB = int(instruction[1])

        elif instruction[0] in ["store", "dstore8", "dstore16"]:
            OpA = registers[instruction[1]] << 16
            try:
                OpB = registers[instruction[2]] << 8
            except KeyError:
                opcode += 1
                OpB = int(instruction[2])

        InstructionValue = (opcode<<24)|OpA|OpB
        HexString += pack(">I", InstructionValue).hex()
        continue

    elif instruction[0] in OtherOpcodes:
        opcode = OtherOpcodes[instruction[0]]
        HexString += pack(">I", opcode).hex()
        continue

# Make a hex dump (sorta) / format
for letter in HexString:
    FinalHexString += letter
    HexCount += 1
    if HexCount % 2 == 0 and HexCount % 8 != 0:
        FinalHexString += " 0x"
    elif HexCount % 8 == 0:
        FinalHexString += "\n0x"


# Display
print()
print("Original Program:")
print("------------------------------------------------------------")
print(program)
print()
print("Assembled Program:")
print("------------------------------------------------------------")
print(FinalHexString[0:-3])
print()
print("Without 0x prefix:")
print("------------------------------------------------------------")
print(FinalHexString.replace("0x", ""))
print("Final stats:")
print("-----------------------------------------")
print(f"Number of bytes: {HexCount//2}")
print(f"Number of instructions: {HexCount//8}")

while not skip:
    print("Enter the file path to write to")
    FilePathForHex = input()
    FilePathForHex = FilePathForHex.replace('"', "")
    try:
        FilePath = Path(FilePathForHex)
        FilePath.write_text(FinalHexString.replace("0x", ""))
        break
    except:
        print("Error handling file path")
        continue
Path(DestFile).write_text(FinalHexString.replace("0x", "")[0:-1]) if skip else False

print("\nHex written without issue!")

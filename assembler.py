#!/usr/bin/python
#
# Copyright (c) 2011 Ivan Vladimirov Ivanov (ivan.vladimirov.ivanov@gmail.com)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.


"""
This module implements the Assembler for the Hack platform described in
Chapter 6 of the book "The Elements of Computing Systems: Building a
Modern Computer from First Principles" (http://www1.idc.ac.il/tecs/).
"""


__author__ = "Ivan Vladimirov Ivanov (ivan.vladimirov.ivanov@gmail.com)"


import os
import re
import sys


_RE_SYMBOL = r"[a-zA-Z_\$\.:][a-zA-Z0-9_\$\.:]*"


def RemoveTrailingComment(line):
  """Removes the trailing comment from a line if one exists."""
  try:
    return line[:line.index("//")]
  except ValueError:
    return line


class AInstruction(object):
  """Responsible for parsing and binary encoding of Addressing Instructions."""
  
  _RE_AINSTRUCTION = re.compile(r"^@(\d*|" + _RE_SYMBOL + ")$")

  def __init__(self, value):
    self.value = value

  def ToBinary(self):
    """Returns the binary encoding of the AInstruction instance."""
    return "0" + self._ToBinary15(self.value)

  def _ToBinary15(self, number):
    """Returns a 15-bit binary representation of number."""
    result = ""
    for i in range(15):
      result = str(number % 2) + result
      number = number / 2
    return result

  @staticmethod
  def Parse(line):
    """Tries to parse a line of Hack assembly into an Addressing Instruction.

    Args:
      line: The line of Hack assembly to parse.

    Returns:
      On success an instance of AInstruction, on failure - False.
    """
    match = re.match(
        AInstruction._RE_AINSTRUCTION, RemoveTrailingComment(line).strip())
    if match:
      return AInstruction._ParseValue(match.group(1))
    else:
      return False

  @staticmethod
  def _ParseValue(value):
    if value.isdigit():
      int_value = int(value)
      return AInstruction(int_value) if 0 <= int_value < (1 << 15) else False
    else:
      return AInstruction(value)


class CInstruction(object):
  """Responsible for parsing and binary encoding of Compute Instructions."""

  _RE_DEST = r"(?:(M|D|MD|A|AM|AD|AMD)=)?"
  _RE_JUMP = r"(?:;(JGT|JEQ|JGE|JLT|JNE|JLE|JMP))?"
  _RE_COMP = (
      r"(0|1|-1|D|A|!D|!A|-D|-A|D\+1|A\+1|D-1|A-1|D\+A|D-A|A-D|D&A|D\|A|"
      r"M|!M|-M|M\+1|M-1|D\+M|D-M|M-D|D&M|D\|M)")
  _RE_CINSTRUCTION = re.compile(r"^%s%s%s$" % (_RE_DEST, _RE_COMP, _RE_JUMP))

  _COMP_TABLE = {
      "0": "0101010",
      "1": "0111111",
      "-1": "0111010",
      "D": "0001100",
      "A": "0110000",
      "!D": "0001101",
      "!A": "0110001",
      "-D": "0001111",
      "D+1": "0011111",
      "A+1": "0110111",
      "D-1": "0001110",
      "A-1": "0110010",
      "D+A": "0000010",
      "D-A": "0010011",
      "A-D": "0000111",
      "D&A": "0000000",
      "D|A": "0010101",
      "M": "1110000",
      "!M": "1110001",
      "-M": "1110011",
      "M+1": "1110111",
      "M-1": "1110010",
      "D+M": "1000010",
      "D-M": "1010011",
      "M-D": "1000111",
      "D&M": "1000000",
      "D|M": "1010101"
  }

  _DEST_TABLE = {
      "": "000",
      "M": "001",
      "D": "010",
      "MD": "011",
      "A": "100",
      "AM": "101",
      "AD": "110",
      "AMD": "111"
  }

  _JUMP_TABLE = {
      "": "000",
      "JGT": "001",
      "JEQ": "010",
      "JGE": "011",
      "JLT": "100",
      "JNE": "101",
      "JLE": "110",
      "JMP": "111"
  }

  def __init__(self, dest, comp, jump):
    self.dest = dest
    self.comp = comp
    self.jump = jump

  def ToBinary(self):
    """Returns the binary encoding of the CInstruction instance."""
    return "111%s%s%s" % (
        CInstruction._COMP_TABLE[self.comp],
        CInstruction._DEST_TABLE[self.dest],
        CInstruction._JUMP_TABLE[self.jump]
    ) 

  @staticmethod
  def Parse(line):
    """Tries to parse a line of Hack assembly into a Compute Instruction.

    Args:
      line: The line of Hack assembly to parse.

    Returns:
      On success an instance of CInstruction, on failure - False.
    """
    match = re.match(
        CInstruction._RE_CINSTRUCTION, RemoveTrailingComment(line).strip())
    if match:
      return CInstruction._ParseMatch(match)
    else:
      return False

  @staticmethod
  def _ParseMatch(match):
    dest = match.group(1) if match.group(1) else ""
    comp = match.group(2)
    jump = match.group(3) if match.group(3) else ""
    return CInstruction(dest, comp, jump)


class LInstruction(object):
  """Responsible for parsing and storing Hack assembly labels."""

  _RE_LINSTRUCTION = re.compile(r"^\((" + _RE_SYMBOL + ")\)$")

  def __init__(self, value):
    self.value = value

  @staticmethod
  def Parse(line):
    """Tries to parse a line of Hack assembly into a Label.

    Args:
      line: The line of Hack assembly to parse.

    Returns:
      On success an instance of LInstruction, on failure - False.
    """
    match = re.match(
        LInstruction._RE_LINSTRUCTION, RemoveTrailingComment(line).strip())
    if match:
      return LInstruction(match.group(1))
    else:
      return False


class EmptyInstruction(object):
  """Represents a no op line of Hack assembly - empty line or comment."""

  @staticmethod
  def Parse(line):
    """Tries to parse a line of Hack assembly into a Label.

    Args:
      line: The line of Hack assembly to parse.

    Returns:
      On success an instance of EmptyInstruction, on failure - False.
    """
    stripped_line = RemoveTrailingComment(line).strip()
    if stripped_line == "":
      return EmptyInstruction()
    else:
      return False

class ErrorInstruction(object):
  """Represents an invalid instruction Hack assembly instruction."""

  def __init__(self, line):
    self.line = line

  @staticmethod
  def Parse(line):
    """Always succeeds in creating an ErrorInstruction instance."""
    return ErrorInstruction(line)


class AssemblerError(Exception):
  """Represents an error specific to the assembly process."""

  def __init__(self, error_message):
    self.error_message = error_message


# This list specifies the order in which the assembler will try to parse
# instructions in a line of Hack assembly.
_INSTRUCTIONS = [
    AInstruction,
    CInstruction,
    LInstruction,
    EmptyInstruction,
    ErrorInstruction]


def ParseInstruction(line):
  """Given a line of Hack assembly, match it with the correct instruction type.

  The order in which the various instruction types are tried is determined by
  the _INSTRUCTIONS table.

  Args:
    line: The line of Hack assembly that is to be parsed.

  Returns:
    An instance of one of the instruction types. In case none of the valid
    instructions are matched an instance of ErrorInstruction is returned.
  """
  for instruction in _INSTRUCTIONS:
    result = instruction.Parse(line)
    if result:
      return result


def Parse(program_lines):
  """Transforms a list of program lines into a list of parsed Instructions.

  Args:
    program_lines: A list of strings representing the list of lines in a
        Hack assembly program.

  Returns:
    A list of parsed program Instructions. There is one instructions for
    each line in the Hack assembly program.

  Raises:
    AssemblerError: At least one of the instructions is an ErrorInstruction.
  """
  program_instructions = map(ParseInstruction, program_lines)
  errors = []
  line_number = 1
  for instruction in program_instructions:
    if instruction.__class__.__name__ == "ErrorInstruction":
      errors.append("Error at line %d: %s" % (line_number, instruction.line))
    line_number += 1
  if len(errors) > 0:
    raise AssemblerError(os.linesep.join(errors))
  return program_instructions


def InitialSymbolTable():
  """Returns a dictionary filled with the initial symbol table values."""
  symbol_table = {
      "SP": 0,
      "LCL": 1,
      "ARG": 2,
      "THIS": 3,
      "THAT": 4,
      "SCREEN": 16384,
      "KBD": 24576
  }
  for i in range(16):
    symbol_table["R%d" % (i,)] = i
  return symbol_table


def AnalyzeSymbols(program_instructions):
  """Creates a symbol table with all variables and labels resolved.

  Args:
    program_instructions: A list of Hack assembly instructions from which
        to create the symbol table.

  Returns:
    A dictionary representing the symbol table with mappings for all variables
    and labels found in the program_instructions, as well as the initial
    symbol mappings for the hack platform.
  """
  symbol_table = InitialSymbolTable()

  # Resolve labels.
  instruction_address = 0
  for instruction in program_instructions:
    itype = instruction.__class__.__name__
    if itype == "LInstruction":
      symbol_table[instruction.value] = instruction_address
    elif itype in ("AInstruction", "CInstruction"):
      instruction_address += 1

  # Resolve variables.
  variable_address = 16
  for instruction in program_instructions:
    if instruction.__class__.__name__ == "AInstruction":
      value = instruction.value
      if type(value) == str and value not in symbol_table:
        symbol_table[value] = variable_address
        variable_address += 1

  return symbol_table


def StripSymbols(program_instructions):
  """Removes all symbolic references from the program_instructions.

  This function not only removes all symbolic references, but also
  removes all instruction types except AInstruction and CInstruction.
  No actual removals are done on the input parameter, instead a new
  list of instructions is returned.

  Args:
    program_instructions: A list of Hack assembly instructions.

  Returns:
    A new list of Hack assembly instructions with all symbolic references
    substituted with thier numerical equivalents, and all none AInstruction
    and CInstruction instances removed.
  """
  stripped_instructions = []
  symbol_table = AnalyzeSymbols(program_instructions)
  for instruction in program_instructions:
    itype = instruction.__class__.__name__
    if itype == "AInstruction":
      if type(instruction.value) == str:
        stripped_instructions.append(
            AInstruction(symbol_table[instruction.value]))
      else:
        stripped_instructions.append(instruction)
    elif itype == "CInstruction":
      stripped_instructions.append(instruction)
  return stripped_instructions


def TranslateToBinary(program_instructions):
  """Transforms a list of instructions into a list of their binary codes.

  Args:
    program_instructions: A list of Hack assembly instructions.

  Returns:
    A list of the binary machine codes for the given instructions.
  """
  return map(lambda i: i.ToBinary(), program_instructions)


def Assemble(program_lines):
  """Transforms the lines of a program into a list of binary instructions.

  Args:
    program_lines: A list of strings representing the lines of a Hack program.

  Returns:
    A list of binary instructions for the assembled program.
  """
  return TranslateToBinary(StripSymbols(Parse(program_lines)))


def main():
  if len(sys.argv) != 2:
    print "Please Specify exactly one argument, the program name."
    return

  asm_file = sys.argv[1]
  if not asm_file.endswith(".asm"):
    print "The file must end with: .asm"
    return

  try:
    with open(asm_file, "r") as asm_program:
      binary_lines = Assemble(asm_program.readlines())
      with open(asm_file[:-4] + ".hack", "w") as hack_program:
        hack_program.write(os.linesep.join(binary_lines))
  except AssemblerError as error:
    print error.error_message
  except IOError as error:
    print error


if __name__ == "__main__":
  main()


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
Test cases for the assembler module.
"""


__author__ = "Ivan Vladimirov Ivanov (ivan.vladimirov.ivanov@gmail.com)"


import unittest
import assembler


class TestAssembler(unittest.TestCase):

  def testParseAInstruction(self):
    result1 = assembler.AInstruction.Parse("@123")
    self.assertTrue(result1 != False)
    self.assertTrue(result1.value == 123)

    result2 = assembler.AInstruction.Parse("@llama")
    self.assertTrue(result2 != False)
    self.assertTrue(result2.value == "llama")

    result3 = assembler.AInstruction.Parse("@123456789")
    self.assertFalse(result3)

    result4 = assembler.AInstruction.Parse("@1llama")
    self.assertFalse(result4)

  def testParseLInstruction(self):
    result1 = assembler.LInstruction.Parse("(foo)")
    self.assertTrue(result1 != False)
    self.assertTrue(result1.value == "foo")

    result2 = assembler.LInstruction.Parse("(foo123..$$:_)")
    self.assertTrue(result2 != False)
    self.assertTrue(result2.value == "foo123..$$:_")

    result3 = assembler.LInstruction.Parse("(1abc)")
    self.assertFalse(result3)

    result4 = assembler.LInstruction.Parse("foo")
    self.assertFalse(result4)

  def testParseCInstruction(self):
    result1 = assembler.CInstruction.Parse("D=M;JMP")
    self.assertTrue(result1 != False)
    self.assertTrue(result1.dest == "D")
    self.assertTrue(result1.comp == "M")
    self.assertTrue(result1.jump == "JMP")

    result2 = assembler.CInstruction.Parse("M=M+1")
    self.assertTrue(result2 != False)
    self.assertTrue(result2.dest == "M")
    self.assertTrue(result2.comp == "M+1")
    self.assertTrue(result2.jump == "")

    result3 = assembler.CInstruction.Parse("0;JMP")
    self.assertTrue(result3 != False)
    self.assertTrue(result3.dest == "")
    self.assertTrue(result3.comp == "0")
    self.assertTrue(result3.jump == "JMP")

    result4 = assembler.CInstruction.Parse("")
    self.assertFalse(result4)

    result5 = assembler.CInstruction.Parse("@1234")
    self.assertFalse(result5)

    result6 = assembler.CInstruction.Parse("llama")
    self.assertFalse(result6)

  def testParseEmptyInstruction(self):
    result1 = assembler.EmptyInstruction.Parse("")
    self.assertTrue(result1 != False)

    result2 = assembler.EmptyInstruction.Parse("   ")
    self.assertTrue(result2 != False)

    result3 = assembler.EmptyInstruction.Parse("// I like pie!")
    self.assertTrue(result3 != False)

    result4 = assembler.EmptyInstruction.Parse("@123")
    self.assertFalse(result4)

  def testParseErrorInstruction(self):
    result1 = assembler.ErrorInstruction.Parse("foo!")
    self.assertTrue(result1 != False)
    self.assertTrue(result1.line == "foo!")

  def testParseInstruction(self):
    result1 = assembler.ParseInstruction("@123")
    self.assertTrue(
        result1 and result1.__class__.__name__ == "AInstruction")

    result2 = assembler.ParseInstruction("@loop")
    self.assertTrue(
        result2 and result2.__class__.__name__ == "AInstruction")

    result3 = assembler.ParseInstruction("M=M+1")
    self.assertTrue(
        result3 and result3.__class__.__name__ == "CInstruction")

    result4 = assembler.ParseInstruction("// I like pie!")
    self.assertTrue(
        result4 and result4.__class__.__name__ == "EmptyInstruction")

    result5 = assembler.ParseInstruction("(loop)")
    self.assertTrue(
        result5 and result5.__class__.__name__ == "LInstruction")

    result6 = assembler.ParseInstruction("Blah")
    self.assertTrue(
        result6 and result6.__class__.__name__ == "ErrorInstruction")

  def testAssemblerError(self):
    program = [ "I like pie!" ]
    self.assertRaises(assembler.AssemblerError, assembler.Assemble, program)

  def testAssembleAdd(self):
    program = [
        "// Computes R0 = 2 + 3",
        "@2",
        "D=A",
        "@3",
        "D=D+A",
        "@0",
        "M=D"]

    result = [
        "0000000000000010",
        "1110110000010000",
        "0000000000000011",
        "1110000010010000",
        "0000000000000000",
        "1110001100001000"]

    self.assertEqual(assembler.Assemble(program), result)

  def testAssembleMax(self):
    program = [
        "// Computes M[2] = max(M[0], M[1])  where M stands for RAM",
        "@0",
        "D=M              // D=first number",
        "@1",
        "D=D-M            // D=first number - second number",
        "@OUTPUT_FIRST",
        "D;JGT            // if D>0 (first is greater) goto output_first",
        "@1",
        "D=M              // D=second number",
        "@OUTPUT_D",
        "0;JMP            // goto output_d",
        "(OUTPUT_FIRST)",
        "@0",
        "D=M              // D=first number",
        "(OUTPUT_D)",
        "@2",
        "M=D              // M[2]=D (greatest number)",
        "(INFINITE_LOOP)",
        "@INFINITE_LOOP",
        "0;JMP            // infinite loop"
    ]

    result = [
        "0000000000000000",
        "1111110000010000",
        "0000000000000001",
        "1111010011010000",
        "0000000000001010",
        "1110001100000001",
        "0000000000000001",
        "1111110000010000",
        "0000000000001100",
        "1110101010000111",
        "0000000000000000",
        "1111110000010000",
        "0000000000000010",
        "1110001100001000",
        "0000000000001110",
        "1110101010000111"
    ]

    self.assertEqual(assembler.Assemble(program), result)

  def testAssembleRect(self):
    program = [
        "// Draws a rectangle at the top left corner of the screen.",
        "// The rectangle is 16 pixels wide and R0 pixels high.",
        "@0",
        "D=M",
        "@INFINITE_LOOP",
        "D;JLE",
        "@counter",
        "M=D",
        "@SCREEN",
        "D=A",
        "@address",
        "M=D",
        "(LOOP)",
        "@address",
        "A=M",
        "M=-1",
        "@address",
        "D=M",
        "@32",
        "D=D+A",
        "@address",
        "M=D",
        "@counter",
        "MD=M-1",
        "@LOOP",
        "D;JGT",
        "(INFINITE_LOOP)",
        "@INFINITE_LOOP",
        "0;JMP"
    ]

    result = [
        "0000000000000000",
        "1111110000010000",
        "0000000000010111",
        "1110001100000110",
        "0000000000010000",
        "1110001100001000",
        "0100000000000000",
        "1110110000010000",
        "0000000000010001",
        "1110001100001000",
        "0000000000010001",
        "1111110000100000",
        "1110111010001000",
        "0000000000010001",
        "1111110000010000",
        "0000000000100000",
        "1110000010010000",
        "0000000000010001",
        "1110001100001000",
        "0000000000010000",
        "1111110010011000",
        "0000000000001010",
        "1110001100000001",
        "0000000000010111",
        "1110101010000111"
    ]

    self.assertEqual(assembler.Assemble(program), result)


if __name__ == "__main__":
  unittest.main()

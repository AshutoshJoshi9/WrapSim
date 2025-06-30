#tests/test_extest.py

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

@cocotb.test()
async def test_extest_mode(dut):
    N = 8  # Extest scan chain width (4 input WBCs + 4 output WBCs)
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Reset sequence
    dut.reset.value = 0
    dut.en.value = 0  # Functional mode (not scan)
    dut.extest_scan_in.value = 0
    await RisingEdge(dut.clk)
    dut.reset.value = 1
    await RisingEdge(dut.clk)
    dut.reset.value = 0
    await RisingEdge(dut.clk)
    
###------------------ EXTEST MODE ------------------------------------
    test_vector = "00000001"  # 8-bit test vector for extest scan chain
    dut._log.info(f"Starting EXTEST mode with test vector: {test_vector}")
    
    # 1) SHIFT-IN (serial shift into extest scan chain)
    dut.en.value = 1  # Enable scan mode
    dut.extest_mode.value = 1  # Enable extest mode
    
    # Shift in the test vector bit by bit
    for i in range(N):
        bit = int(test_vector[N-1-i])  # MSB first
        dut.extest_scan_in.value = bit
        await RisingEdge(dut.clk)
        dut._log.info(f"Shifted in bit {i}: {bit}")
    
    # 2) CAPTURE (functional cycles for left and right cores)
    dut.en.value = 0  # Functional mode
    dut.extest_mode.value = 0  # Disable extest mode for capture
    
    # Run capture cycles (parameterizable)
    capture_cycles = 1  # Can be adjusted
    for cycle in range(capture_cycles):
        await RisingEdge(dut.clk)
        dut._log.info(f"Capture cycle {cycle + 1} completed")
    
    # 3) SHIFT-OUT (serial shift out from extest scan chain)
    dut.en.value = 1  # Enable scan mode
    dut.extest_mode.value = 1  # Enable extest mode
    
    # Shift out the signature
    signature = ""
    for i in range(N):
        bit = dut.extest_scan_out.value
        signature = str(bit) + signature  # LSB first
        await RisingEdge(dut.clk)
        dut._log.info(f"Shifted out bit {i}: {bit}")
    
    dut._log.info(f"EXTEST signature: {signature}")

@cocotb.test()
async def test_extest_multiple_vectors(dut):
    """Test multiple extest vectors"""
    N = 8
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Reset sequence
    dut.reset.value = 0
    dut.en.value = 0
    dut.extest_scan_in.value = 0
    await RisingEdge(dut.clk)
    dut.reset.value = 1
    await RisingEdge(dut.clk)
    dut.reset.value = 0
    await RisingEdge(dut.clk)
    
    # Test multiple vectors
    test_vectors = [
        "00000000",  # all zeros
        "11111111",  # all ones
        "10000000",  # walking one
        "01000000",
        "00100000",
        "00010000",
        "00001000",
        "00000100",
        "00000010",
        "00000001",
        "01111111",  # walking zero
        "10101010",  # alternating
        "01010101",  # alternating
        "11001100",  # double bits
        "00110011",  # double bits
        "11110000",  # upper half
        "00001111",  # lower half
        "10011001",  # random
        "01100110",  # random
        "00111100",  # random
    ]
    

    
    for test_vector in test_vectors:
        dut._log.info(f"\n=== Testing EXTEST vector: {test_vector} ===")
        
        # Shift in
        dut.en.value = 1
        dut.extest_mode.value = 1
        for i in range(N):
            bit = int(test_vector[N-1-i])
            dut.extest_scan_in.value = bit
            await RisingEdge(dut.clk)
        
        # Capture
        dut.en.value = 0
        dut.extest_mode.value = 0
        await RisingEdge(dut.clk)  # 1 capture cycle
        
        # Shift out
        dut.en.value = 1
        dut.extest_mode.value = 1
        signature = ""
        for i in range(N):
            bit = dut.extest_scan_out.value
            signature = str(bit) + signature
            await RisingEdge(dut.clk)
        
        dut._log.info(f"Input: {test_vector} -> Output: {signature}") 
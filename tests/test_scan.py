#tests/test_scan.py

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

@cocotb.test()
async def test_counter_functional(dut):
    N = 4  # Counter width
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Reset sequence
    dut.reset.value = 0
    dut.en.value = 0  # Functional mode (not scan)
    getattr(dut, "in").value = 0
    await RisingEdge(dut.clk)
    dut.reset.value = 1
    await RisingEdge(dut.clk)
    dut.reset.value = 0
    await RisingEdge(dut.clk)
    
###------------------ INTEST MODE ------------------------------------
    test_vector = "0010"
    # 1) SHIFT-IN (parallel load via the 4-bit `in` port)
    dut.en.value = 1
    in_bus = getattr(dut, 'in')
    in_bus.value = int(test_vector, 2)
    await RisingEdge(dut.clk)


    # 2) CAPTURE (two functional cycles with en=0)
    dut.en.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    # 3) SHIFT-OUT (read back via the 4-bit `out` port)
    dut.en.value = 1
    await RisingEdge(dut.clk)

    out_bus = dut.out
    sig_int = int(out_bus.value)
    captured = format(sig_int, f"0{N}b")
    dut._log.info(f"Captured signature: {captured}")

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
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    # Test: apply a sequence of values to 'in' and check 'out'
    # We'll use the counter as a loadable register: in[3:0] is loaded when en=1, otherwise it should count
    # But your netlist seems to use 'in' as scan input when en=1, so for functional mode, en=0



# Makefile for cocotb-based scan test of net1.v

# --------------------------------------------------------------------
# 1) Tell cocotb how to find your design and test
# --------------------------------------------------------------------
# Top‐level Verilog module (must match your testbench instantiation)
TOPLEVEL      = tb   
# Language of the DUT
TOPLEVEL_LANG = verilog    
# Verilog sources: your DUT + the tb wrapper
VERILOG_SOURCES = simple_counter.v lib_cells.v testbench.v
# Python test module (under tests/test_scan.py, no “.py”)
MODULE        = tests.test_scan

# --------------------------------------------------------------------
# 2) Include the cocotb-provided build rules
# --------------------------------------------------------------------
# cocotb-config should be on your PATH (comes with `pip install cocotb`)
include $(shell cocotb-config --makefiles)/Makefile.sim

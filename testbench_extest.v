`timescale 1ns/1ps

module tb_extest;
  // width of extest scan chain (4 input WBCs + 4 output WBCs)
  localparam N = 8;

  // Testbench signals
  reg         clk    = 0;
  reg         reset;       // no default here
  reg         en     = 1;
  reg         extest_mode = 0;  // Extest mode control
  reg         extest_scan_in = 0;  // Serial scan input
  wire        extest_scan_out;     // Serial scan output
  reg  [3:0]  in    = 0;   // Original 4-bit input (for reference)
  wire [3:0]  out;         // Original 4-bit output (for reference)


  initial begin
    $dumpfile("wave_extest.vcd");
    $dumpvars(0, tb_extest);
  end

  // Clock generator: 10 ns period
  always #5 clk = ~clk;

  //-------------------------------------------------------------------------
  // DUT instantiation - using the extest wrapper
  //-------------------------------------------------------------------------
  extest_wrapper u_dut (
    .clk   (clk),
    .reset (reset),   // drives RN in your SDFFRX1 cells
    .en    (en),
    .extest_mode (extest_mode),
    .extest_scan_in (extest_scan_in),
    .extest_scan_out (extest_scan_out),
    .in    (in),      // Original inputs (for reference)
    .out   (out)      // Original outputs (for reference)
  );

  //-------------------------------------------------------------------------
  // Reset & VCD dump
  //-------------------------------------------------------------------------
  initial begin
    // assert reset (active-low RN) for two cycles
    reset = 1;       
    #1;              // ensure reset=1 at time=0+δ
    @(posedge clk);  // cycle 1
    reset = 0;       // de-assert reset (RN=0 → normal operation)
  end

  //-------------------------------------------------------------------------
  // Monitor for debugging
  //-------------------------------------------------------------------------
  initial begin
    $monitor("Time=%0t clk=%b reset=%b en=%b extest_mode=%b scan_in=%b scan_out=%b in=%b out=%b",
             $time, clk, reset, en, extest_mode, extest_scan_in, extest_scan_out, in, out);
  end

endmodule 
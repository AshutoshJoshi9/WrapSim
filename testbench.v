`timescale 1ns/1ps

module tb;
  // width of your scan chain
  localparam N = 4;

  // Testbench signals
  reg         clk    = 0;
  reg         reset;       // no default here
  reg         en     = 1;
  reg  [N-1:0] in    = 0;
  wire [N-1:0] out;


  initial begin
    $dumpfile("wave.vcd");
    $dumpvars(0, tb);
  end



  // Clock generator: 10 ns period
  always #5 clk = ~clk;

  //-------------------------------------------------------------------------
  // DUT instantiation
  //-------------------------------------------------------------------------
  top u_dut (
    .clk   (clk),
    .reset (reset),   // drives RN in your SDFFRX1 cells
    .en    (en),
    .in    (in),
    .out   (out)
  );

  //-------------------------------------------------------------------------
  // Reset & VCD dump
  //-------------------------------------------------------------------------
  initial begin
    // assert reset (active-low RN) for two cycles
    reset = 1;       
    #1;              // ensure reset=1 at time=0+δ
    @(posedge clk);  // cycle 1
    //@(posedge clk);  // cycle 2
    reset = 0;       // de-assert reset (RN=0 → normal operation)

  end

endmodule


module counter(clk, reset, en, in, out);
  input clk, reset, en;
  input [3:0] in;
  output [3:0] out;
  wire clk, reset, en;
  wire [3:0] in;
  wire [3:0] out;
  wire UNCONNECTED, UNCONNECTED0, UNCONNECTED1, UNCONNECTED2, n_0, n_1,
       n_2, n_3;
  wire n_4, n_5, n_6;

  SDFFRX1 \count_reg[3]  (.RN (n_0), .CK (clk), .D (n_6), .SI (in[3]),
                          .SE (en), .Q (out[3]), .QN (UNCONNECTED));
  SDFFRX1 \count_reg[2]  (.RN (n_0), .CK (clk), .D (n_5), .SI (in[2]),
                          .SE (en), .Q (out[2]), .QN (UNCONNECTED0));
  OAI2BB2XL g372_2398 (.A0N (out[3]), .A1N (n_4), .B0 (n_4), .B1 (out[3]), .Y (n_6));
  SDFFRX1 \count_reg[1]  (.RN (n_0), .CK (clk), .D (n_3), .SI (in[1]),
                          .SE (en), .Q (out[1]), .QN (UNCONNECTED1));
  AOI21XL g374_5107 (.A0 (in[1]), .A1 (out[2]), .B0 (n_4), .Y (n_5));
  NAND2XL g375_6260 (.A (n_1), .B (out[1]), .Y (n_4));
  SDFFRX1 \count_reg[0]  (.RN (n_0), .CK (clk), .D (n_2), .SI (in[0]),
                          .SE (en), .Q (out[0]), .QN (UNCONNECTED2));
  AOI2BB1XL g377_4319 (.A0N (out[1]), .A1N (n_3), .B0 (n_1), .Y (n_2));
  OAI2BB2XL g378_8428 (.A0N (in[0]), .A1N (en), .B0 (out[0]), .B1 (en), .Y (n_3));
  AND2XL g379_5526 (.A (out[1]), .B (out[0]), .Y (n_1));
  CLKINVX1 g380 (.A (reset), .Y (n_0));
endmodule

module top(clk, reset, en, in, out);
  input clk, reset, en;
  input [3:0] in;
  output [3:0] out;
  wire clk, reset, en;
  wire [3:0] in; 
  wire [3:0] out;
  counter counter_inst(.clk (clk), .reset (reset), .en (en), .in (in), .out (out));
endmodule

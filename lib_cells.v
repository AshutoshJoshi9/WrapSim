// lib_cells.v
//-----------------------------------------------------------------------------
//  Behavioral stubs for your standard cells, so Icarus can elaborate net1.v
//-----------------------------------------------------------------------------

module SDFFRX1 (
    input  D,
    input  SE,
    input  SI,
    input  CK,
    input RN,
    output Q,
    output QN
);
  reg state;
  always @(posedge CK or negedge RN) begin
    if (!RN) state <= 1'b0;
    else if (SE) state <= SI;
    else state <= D;
  end
  assign Q  = state;
  assign QN = ~state;
endmodule

module DFFRX1 (
    input D,
    input CK,
    input RN,
    output reg Q,
    output QN
);
  always @(posedge CK or negedge RN) begin
    if (!RN) Q <= 1'b0;
    else Q <= D;
  end
  assign QN = ~Q;
endmodule

module NAND2XL (
    input  A,
    input  B,
    output Y
);
  assign Y = ~(A & B);
endmodule

module AND2XL (
    input  A,
    input  B,
    output Y
);
  assign Y = A & B;
endmodule

module OAI2BB2XL (
    input  A0N,
    input  A1N,
    input  B0,
    input  B1,
    output Y
);
  // Y = ~((~(A0N & A1N)) & (B0 & B1))
  assign Y = ~((~(A0N & A1N)) & (B0 | B1));
endmodule

module AOI2BB1XL (
    input  A0N,
    input  A1N,
    input  B0,
    output Y
);
  // Y = ~((~(A0N | A1N)) | B0)
  assign Y = ~((~(A0N | A1N)) | B0);
endmodule

module CLKINVX1 (
    input  A,
    output Y
);
  assign Y = ~A;
endmodule


module AOI21XL (
    input A0,
    input A1,
    input B0,
    output Y
);
    assign Y = ~(B0 | (A0 & A1));
endmodule

module XOR2XL (
    input A,
    input B,
    output Y
);
    assign Y = A ^ B;
endmodule
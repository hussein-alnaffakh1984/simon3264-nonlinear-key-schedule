`timescale 1ns/1ps
module tb; reg [15:0] k0,k1,k2,k3,exp; reg z; wire [15:0] o; integer f,n,bad,r;
  ks_round_v3 u(.k0(k0),.k1(k1),.k2(k2),.k3(k3),.z(z),.o(o));
  initial begin f=$fopen("rtl/vec.hex","r"); n=0; bad=0;
    while(!$feof(f)) begin r=$fscanf(f,"%h %h %h %h %b %h\n",k0,k1,k2,k3,z,exp); if(r==6) begin #1; n=n+1; if(o!==exp) bad=bad+1; end end
    $display("vectors %0d mismatches %0d",n,bad); $finish; end
endmodule

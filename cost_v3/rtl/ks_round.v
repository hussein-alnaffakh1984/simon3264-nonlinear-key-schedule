// Combinational logic of ONE key-schedule round update for Simon 32/64.
// k0 = rk[i-4], k1 = rk[i-3], k2 = rk[i-2], k3 = rk[i-1], z = z0[i-4]  ->  o = rk[i]
// rk[i] = ~k0 ^ t ^ c_i with c_i = z ^ 3  ==  k0 ^ t ^ 16'hFFFC ^ z

module nl16(input [15:0] w, output [15:0] o);          // shift left by one, LSB <- n1 (bit 15 dropped)
  wire n1 = ((w[15] & w[7]) | w[3]) & (w[13] | w[3]);
  assign o = {w[14:0], n1};
endmodule

module ks_round_std(input [15:0] k0, k1, k2, k3, input z, output [15:0] o);
  wire [15:0] t = {k3[2:0], k3[15:3]} ^ k1;             // ROR3(k3) ^ k1
  wire [15:0] u = t ^ {t[0], t[15:1]};                  // t ^ ROR1(t)
  assign o = k0 ^ u ^ {15'h7FFE, z};
endmodule

module ks_round_v2(input [15:0] k0, k1, k2, k3, input z, output [15:0] o);
  wire [15:0] a;
  nl16 n(.w(k1), .o(a));
  wire [15:0] t = {k3[2:0], k3[15:3]} ^ a;
  wire [15:0] u = t ^ {t[4:0], t[15:5]};                // t ^ ROR5(t)
  assign o = k0 ^ u ^ {15'h7FFE, z};
endmodule

module ks_round_paper(input [15:0] k0, k1, k2, k3, input z, output [15:0] o);
  wire parity = k3[7] ^ k2[4] ^ k1[9] ^ k0[11];
  wire flag   = |((k0 & k1 & k2 & k3) | ~(k0 | k1 | k2 | k3));   // some bit position equal in all four words
  wire sel    = parity | flag;
  wire [15:0] n;
  nl16 nn(.w(k1), .o(n));
  wire [15:0] a = sel ? n : k1;
  wire [15:0] t = {k3[2:0], k3[15:3]} ^ a;
  wire [15:0] u = t ^ {t[4:0], t[15:5]};
  assign o = k0 ^ u ^ {15'h7FFE, z};
endmodule

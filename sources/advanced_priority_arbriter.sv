`timescale 1ns/1ps

module advanced_priority_arbiter #(
    parameter int N          = 4,
    parameter int PRIO_WIDTH = 4,
    parameter int CLASS_W    = 2,
    parameter int FAIR_K     = 8          // max wait cycles
)(
    input  logic               clk,
    input  logic               reset,      // Active-LOW
    input  logic [N-1:0]       req,
    input  logic [CLASS_W-1:0] class_prio [N],
    input  logic               gnt_ready,

    output logic [N-1:0]       gnt,
    output logic               gnt_valid
);

    localparam logic [PRIO_WIDTH-1:0] MAX_PRIO = {PRIO_WIDTH{1'b1}};
    localparam int IDX_W = $clog2(N);

    // ------------------------------------------------------------
    // State
    // ------------------------------------------------------------
    logic [PRIO_WIDTH-1:0] eff_prio [N];
    logic [PRIO_WIDTH-1:0] eff_prio_n [N];

    logic [$clog2(FAIR_K+1)-1:0] wait_cnt [N];

    logic [IDX_W-1:0] hold_idx;
    logic             hold_active;

    // ------------------------------------------------------------
    // Arbitration (combinational)
    // ------------------------------------------------------------
    logic [IDX_W-1:0] sel_idx;
    logic             sel_found;

    always @(*) begin
        sel_found = 1'b0;
        sel_idx   = '0;

        for (int i = 0; i < N; i++) begin
            if (req[i]) begin
                if (!sel_found ||(wait_cnt[i] >= FAIR_K) ||(class_prio[i] > class_prio[sel_idx]) ||
                    ((class_prio[i] == class_prio[sel_idx]) &&
                     (eff_prio[i] > eff_prio[sel_idx]))) begin
                    sel_found = 1'b1;
                    sel_idx   = i;
                end
            end
        end
    end

    // ------------------------------------------------------------
    // Grant output logic
    // ------------------------------------------------------------
    always @(*) begin
        gnt       = '0;
        gnt_valid = 1'b0;

        if (hold_active) begin
            gnt[hold_idx] = 1'b1;
            gnt_valid     = 1'b1;
        end
        else if (sel_found) begin
            gnt[sel_idx] = 1'b1;
            gnt_valid    = 1'b1;
        end
    end

    // ------------------------------------------------------------
    // Next-state priority & fairness logic
    // ------------------------------------------------------------
    always @(*) begin
        for (int i = 0; i < N; i++) begin
            eff_prio_n[i] = eff_prio[i];

            if (!hold_active) begin
                // granted → reset
                if (gnt[i] && gnt_ready) begin
                    eff_prio_n[i] = '0;
                end
                // aging
                else if (req[i] && eff_prio[i] < MAX_PRIO) begin
                    eff_prio_n[i] = eff_prio[i] + 1'b1;
                end
            end
        end
    end

    // ------------------------------------------------------------
    // Sequential logic
    // ------------------------------------------------------------
    always_ff @(posedge clk or negedge reset) begin
        if (!reset) begin
            hold_active <= 1'b0;
            hold_idx    <= '0;
            gnt_valid   <= 1'b0;

            for (int i = 0; i < N; i++) begin
                eff_prio[i] <= '0;
                wait_cnt[i] <= '0;
            end
        end
        else begin
            // -----------------------------
            // Grant hold logic
            // -----------------------------
            if (gnt_valid && !gnt_ready) begin
                hold_active <= 1'b1;
            end
            else begin
                hold_active <= 1'b0;
            end

            if (!hold_active && sel_found) begin
                hold_idx <= sel_idx;
            end

            // -----------------------------
            // Update priorities
            // -----------------------------
            for (int i = 0; i < N; i++) begin
                eff_prio[i] <= eff_prio_n[i];
            end

            // -----------------------------
            // Fairness counters
            // -----------------------------
            for (int i = 0; i < N; i++) begin
                if (!hold_active) begin
                    if (req[i] && !(gnt[i] && gnt_ready)) begin
                        if (wait_cnt[i] < FAIR_K)
                            wait_cnt[i] <= wait_cnt[i] + 1'b1;
                    end
                    else begin
                        wait_cnt[i] <= '0;
                    end
                end
            end
        end
    end

endmodule
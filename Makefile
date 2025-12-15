# Makefile for running cocotb tests

TOPLEVEL_LANG = verilog
SIM = icarus

VERILOG_SOURCES = $(PWD)/sources/priority_arbiter.sv
TOPLEVEL = priority_arbiter
MODULE = test_priority_arbiter_hidden

include $(shell cocotb-config --makefiles)/Makefile.sim


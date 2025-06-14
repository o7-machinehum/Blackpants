VENV?=.venv
VENV_ACTIVATE=. $(VENV)/bin/activate
PIP=$(VENV)/bin/pip
.PHONY: clean prepare drc_carrier gerbers_carrier schematic_carrier drc_m2 gerbers_m2 schematic_m2
.ONESHELL:

prepare:
	python -m venv --system-site-packages .venv
	$(VENV_ACTIVATE)
	$(PIP) install --quiet kikit
remove_env:
	rm -rf $(VENV)
clean:
	rm -rf Carrier/production M2/production Carrier/pdfs M2/pdfs

# Carrier board
drc_carrier:
	[ -d ".venv" ] && $(VENV_ACTIVATE); \
	kikit drc run ./Carrier/badgeCarrierCard.kicad_pcb
gerbers_carrier:
	[ -d ".venv" ] && $(VENV_ACTIVATE); \
	kikit fab jlcpcb --assembly --schematic Carrier/badgeCarrierCard.kicad_sch Carrier/badgeCarrierCard.kicad_pcb Carrier/production
schematic_carrier:
	kicad-cli sch export pdf --output Carrier/pdfs/schematic.pdf Carrier/badgeCarrierCard.kicad_sch
pdfs_carrier:
	kicad-cli pcb export pdf --mode-separate --output Carrier/pdfs Carrier/badgeCarrierCard.kicad_pcb -l "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,Edge.Cuts,F.Fab,B.Fab"

# M2 board
drc_m2:
	[ -d ".venv" ] && $(VENV_ACTIVATE); \
	kikit drc run ./M2/P4_M.2_B+M-key.kicad_pcb
gerbers_m2:
	[ -d ".venv" ] && $(VENV_ACTIVATE); \
	kikit fab jlcpcb --assembly --schematic M2/P4_M.2_B+M-key.kicad_sch M2/P4_M.2_B+M-key.kicad_pcb M2/production
schematic_m2:
	kicad-cli sch export pdf --output M2/pdfs/schematic.pdf M2/P4_M.2_B+M-key.kicad_sch
pdfs_m2:
	kicad-cli pcb export pdf --mode-separate --output M2/pdfs M2/P4_M.2_B+M-key.kicad_pcb -l "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,Edge.Cuts,F.Fab,B.Fab"
